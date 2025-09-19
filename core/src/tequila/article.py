from prompt_bottle import render
from pydantic_ai.models import Model
from pydantic_ai import Agent, TextOutput
from pydantic import BaseModel, Field, TypeAdapter
from tequila.utils import value_error_to_retry
import re
import yaml
from typing import Literal, Annotated, TypeAlias

PROMPT = """
<Instruction>
Create a fictional Wikipedia-style article following the format below:

# Title

...(Overview/Summary)...

## (Section Header)

...(Section Content)...

The article should be written in Markdown format. 
All fictional terms (including names, places, events, concepts, etc.) 
must be wrapped in <em></em> tags, to distinguish them from real-world terms. 

</Instruction>

<Guidelines>
- Use consistent language ({{lang}}).
- Write in Wikipedia-style tone: neutral, encyclopedic, and informative.
- Include multiple sections for depth and structure.
- Be creative while maintaining logical consistency. Avoid repetitive language and unnecessary new term creation.
- Wrap all fictional terms in <em></em> tags, including both existing and newly created ones.
</Guidelines>

<div role="user">
{% if style_inst %}
<Style>{{style_inst}}</Style>
{% endif %}
{% if context %}
<Context>{{context}}</Context>
{% endif %}
<TaskArticle>{{title}}</TaskArticle>
{% if alt_title %}
<AltTitle>{{alt_title}}</AltTitle>
{% endif %}
</div>
"""


class Section(BaseModel):
    title: str
    content: str


class ProtoArticle(BaseModel):
    kind: Literal["proto_article"] = "proto_article"
    title: str
    alt_title: set[str] = Field(default_factory=set)


class Article(ProtoArticle):
    kind: Literal["article"] = "article"
    summary: str = ""
    sections: list[Section] = Field(default_factory=list)
    links: dict[str, set[str]] = Field(default_factory=dict)

    @classmethod
    def validate(cls, text: str, strict: bool = True):
        """
        Validate markdown text, with or without prefix YAML frontmatter.
        If strict=True and invalid, raise ValueError with description.
        If strict=False, return Article with whatever information can be extracted.
        """
        # Check basic markdown structure
        if not text.strip():
            if strict:
                raise ValueError("Text cannot be empty")
            else:
                return cls(title="")

        # Parse YAML frontmatter if present
        frontmatter = {}
        content_text = text.strip()

        if text.strip().startswith("---"):
            # Split frontmatter and content
            parts = text.strip().split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter_text = parts[1].strip()
                    content_text = parts[2].strip()
                    if frontmatter_text:
                        frontmatter = yaml.safe_load(frontmatter_text) or {}
                except yaml.YAMLError as e:
                    if strict:
                        raise ValueError(f"Invalid YAML frontmatter: {e}")
                    # Continue with empty frontmatter if not strict

        lines = content_text.split("\n")

        # Extract title - first check frontmatter, then look for first # heading
        title = None
        title_line_idx = None

        # Check frontmatter for title
        if "title" in frontmatter:
            title = str(frontmatter["title"]).strip()

        # look for # heading
        for i, line in enumerate(lines):
            if line.strip().startswith("# "):
                # YAML frontmatter title takes precedence over # heading title
                if not title:
                    title = line.replace("# ", "").strip()
                title_line_idx = i
                break

        if not title:
            if strict:
                raise ValueError(
                    "Text must have a title either in YAML frontmatter or as a main heading using '# ' format"
                )
            else:
                return cls(title="")

        # Check for sections (should have ## headings)
        section_lines = []
        for i, line in enumerate(lines):
            if line.strip().startswith("## "):
                section_lines.append(i)

        has_sections = len(section_lines) > 0
        if not has_sections and strict:
            raise ValueError(
                "Text must contain at least one section with '## ' heading"
            )

        # Extract summary (content between title and first section)
        summary_start = (title_line_idx + 1) if title_line_idx is not None else 0
        summary_end = section_lines[0] if section_lines else len(lines)

        summary_lines = []
        for i in range(summary_start, summary_end):
            if i < len(lines) and lines[i].strip():
                summary_lines.append(lines[i])

        summary = "\n".join(summary_lines).strip()

        if not strict and not has_sections:
            return cls(title=title, summary=summary, sections=[])

        if not summary and strict:
            if title_line_idx is not None and (
                not section_lines or section_lines[0] <= title_line_idx + 1
            ):
                raise ValueError(
                    "Text must have summary content between title and first section"
                )
            elif not summary_lines:
                raise ValueError("Summary section cannot be empty")

        # Extract all <em> tags and their content (for validation only)
        if strict:
            em_pattern = r"<em>(.*?)</em>"
            em_matches = re.findall(em_pattern, content_text)

            if not em_matches:
                raise ValueError(
                    "Text must contain fictional terms wrapped in <em></em> tags as required by prompt"
                )

        # Extract sections
        sections = []

        if section_lines:
            for i, section_start in enumerate(section_lines):
                # Determine section end
                section_end = (
                    section_lines[i + 1] if i + 1 < len(section_lines) else len(lines)
                )

                # Extract section title
                section_title = lines[section_start].replace("## ", "").strip()

                # Extract section content
                section_content_lines = []
                for j in range(section_start + 1, section_end):
                    if j < len(lines) and lines[j].strip():
                        section_content_lines.append(lines[j])

                section_content = "\n".join(section_content_lines).strip()

                if not section_content:
                    if strict:
                        raise ValueError(f"Section '{section_title}' cannot be empty")
                    else:
                        break

                # Add section even if content is empty in non-strict mode
                sections.append(Section(title=section_title, content=section_content))

        if not sections and strict:
            raise ValueError("Text must contain at least one section")

        # Create and return Article instance
        return cls(
            title=title,
            summary=summary,
            sections=sections,
        )

    @property
    def content(self) -> str:
        return f"# {self.title}\n\n{self.summary}\n\n" + "\n\n".join(
            [f"## {section.title}\n\n{section.content}" for section in self.sections]
        )

    def dump_md(self) -> str:
        return f"---\n{yaml.dump(self.model_dump(mode='json', exclude={'summary', 'sections'}), allow_unicode=True)}\n---\n\n{self.content}"

    def get_links(self) -> set[str]:
        return {link for link in self.links}


ProtoOrArticleType: TypeAlias = Annotated[ProtoArticle | Article, Field(discriminator="kind")]
proto_or_article_adapter = TypeAdapter[ProtoOrArticleType](ProtoOrArticleType)


async def write_article(
    model: Model,
    proto: ProtoArticle,
    lang: str,
    *,
    context: str | None = None,
    style_inst: str | None = None,
    streaming: float | bool = False,
):
    prompt = render(
        PROMPT,
        model=model,
        title=proto.title,
        alt_title=", ".join(proto.alt_title) if proto.alt_title else None,
        context=context,
        style_inst=style_inst,
        lang=lang,
    )

    agent = Agent(
        model=model,
        output_type=TextOutput(
            value_error_to_retry(Article.validate),
        ),
        output_retries=3,
    )

    if not streaming:
        res = (await agent.run(message_history=prompt)).output
    else:
        async with agent.run_stream(message_history=prompt) as stream:
            async for article_text in stream.stream_text(
                debounce_by=0.1 if streaming==True else streaming # noqa: E712
            ):
                tmp = Article.validate(article_text, strict=False)
                tmp.title = proto.title
                tmp.alt_title = proto.alt_title
                yield tmp
            res = await stream.get_output()
            res.title = proto.title
            res.alt_title = proto.alt_title

    yield res


async def main():
    from pydantic_ai.models.openai import OpenAIChatModel
    from rich.live import Live
    from rich.text import Text
    from rich.panel import Panel
    import logfire

    logfire.configure()
    logfire.instrument_pydantic_ai()
    model = OpenAIChatModel(
        model_name="deepseek/deepseek-chat-v3.1", provider="openrouter"
    )

    with Live(Text("Starting..."), refresh_per_second=10) as live:
        async for part in write_article(
            model,
            ProtoArticle(title="黑林村瘟疫"),
            context="（1348–1351）",
            style_inst="中世纪欧洲风格，注意地名不能叫做‘欧洲’",
            lang="中文",
            streaming=True,
        ):
            # Create a panel with the current content
            content = Panel(
                part.content, title="Output", title_align="left", border_style="blue"
            )
            live.update(content)
            res = part

    with open("dev/article.md", "w") as f:
        f.write(res.dump_md())


if __name__ == "__main__":
    from dotenv import load_dotenv
    import asyncio

    load_dotenv()
    asyncio.run(main())
