from prompt_bottle import render
from pydantic_ai.models import Model
from pydantic_ai import Agent, TextOutput
from pydantic import BaseModel
import re

from tequila.article import Article
from tequila.utils import value_error_to_retry
from qwq_tag import QwqTag

PROMPT = """
<Instruction>
分析文中所有 em 标记的条目，识别并合并同义变体。

## 合并规则

**本体条目 (Ontology)**：
- 文章标题必须作为本体条目（即使未被 em 标记）
- 多语言专有名词以正文语言{% if lang %}({{lang}}){% endif %}为本体，其他语言为变体
- 每个概念只能有一个本体条目

**变体条目 (Alternative)**：
- 语义相同或变体形式：大小写变体、拼写变体、翻译对应等
- 用语不同但指代同一概念的别名
- 变体条目不能再作为本体出现

**约束条件**：
- 每个条目只能出现一次
- 包含关系 != 同义关系
- 变体必须与本体语义完全一致

## 输出格式

```xml
<onto idx="1">本体条目名</onto>
<alt of="1">变体条目名</alt>
<alt of="1">另一个变体</alt>
<onto idx="2">另一个本体</onto>
<alt of="2">其变体</alt>
<onto>无变体的独立条目</onto>
```

**说明**：
- `onto` 标记本体条目，有变体时需要 `idx` 属性作为唯一标识
- `alt` 标记变体条目，`of` 属性指向对应本体的 `idx`
- 无变体的独立条目可省略 `idx` 属性，有变体的本体条目必须有 `idx` 属性
- 直接输出 xml 格式的结果

</Instruction>
<div role="user">
{{text_}}
</div>
"""


class _Link(BaseModel):
    name: str
    alter: list[str] | None = None
    alt_of: str | None = None

    @classmethod
    def validate(cls, text: str) -> list["_Link"]:
        try:
            tags = QwqTag.from_str(text)
        except Exception as e:
            raise ValueError(f"Invalid XML/HTML format: {e}")

        if not tags:
            raise ValueError("Empty input text")

        links: list[_Link] = []
        onto_links: dict[str, _Link] = {}  # Map idx to onto Link objects

        for tag in tags:
            if isinstance(tag, str):
                continue

            if tag.name == "onto":
                # Process ontology terms
                idx = tag.attr.get("idx")

                word = tag.content_text.strip()
                if not word:
                    raise ValueError("Empty <onto> tag found")

                if word in [x.name for x in links]:
                    raise ValueError(f"Duplicate link: {word}")

                # Create the main link
                main_link = _Link(name=word, alter=[])
                links.append(main_link)

                # Only store in onto_links if it has an idx (for potential alt references)
                if idx:
                    onto_links[idx] = main_link

            elif tag.name == "alt":
                # Process alternative terms
                of_attr = tag.attr.get("of")
                if not of_attr:
                    raise ValueError("<alt> tag missing required 'of' attribute")

                alter_text = tag.content_text.strip()
                if not alter_text:
                    raise ValueError("Empty <alt> tag found")

                # Find the corresponding onto link
                if of_attr not in onto_links:
                    raise ValueError(
                        f"<alt> tag references unknown onto idx: {of_attr}"
                    )

                onto_link = onto_links[of_attr]

                # Skip if alter is same as its ontology
                if alter_text == onto_link.name:
                    continue

                if alter_text in [x.name for x in links]:
                    raise ValueError(f"Duplicate link: {alter_text}")

                # Add to onto link's alter list
                if onto_link.alter is None:
                    onto_link.alter = []
                onto_link.alter.append(alter_text)

                # Create alter link that points to the onto link
                alter_link = _Link(name=alter_text, alter=None, alt_of=onto_link.name)
                links.append(alter_link)

            else:
                raise ValueError(
                    f"Unexpected tag: <{tag.name}>. Only <onto> and <alt> tags are allowed"
                )

        if not links:
            raise ValueError("No <onto> tags found in the input")

        return links


async def _link_parse(model: Model, text: str, lang: str) -> list[_Link]:
    prompt = render(PROMPT, model=model, text_=text, lang=lang)
    agent = Agent(
        model=model,
        output_type=TextOutput(
            value_error_to_retry(_Link.validate),
        ),
        output_retries=3,
    )
    res = (await agent.run(message_history=prompt)).output
    return res


async def parse_links(model: Model, article: Article, lang: str):
    res = await _link_parse(model, article.content, lang)

    # The title must be an ontology term
    title_link = None
    for link in res:
        if link.name == article.title:
            title_link = link
            break

    if title_link and title_link.alt_of is not None:
        to_replace = title_link.alt_of
        title_link.alt_of = None
        title_link.alter = [to_replace]

        to_replace_link = [x for x in res if x.name == to_replace][0]
        to_replace_link.alter = []
        to_replace_link.alt_of = title_link.name

        for i in res:
            if i.alt_of == to_replace and i.name != title_link.name:
                i.alt_of = title_link.name
                title_link.alter.append(i.name)

    # Update alt_title of the article
    if title_link:
        article.alt_title.update(title_link.alter or [])

    for link in res:
        if link.name != article.title and link.alt_of is None:
            article.links[link.name] = set(link.alter) if link.alter else set()

    def process_text(text: str) -> str:
        return re.sub(r"<em>(.*?)</em>", r"\1", text)

    # Process the article's summary
    article.summary = process_text(article.summary)

    # Process each section's content
    for section in article.sections:
        section.content = process_text(section.content)


async def main():
    from pydantic_ai.models.openai import OpenAIChatModel
    import logfire

    logfire.configure()
    logfire.instrument_pydantic_ai()
    model = OpenAIChatModel(
        model_name="deepseek/deepseek-chat-v3.1", provider="openrouter"
    )
    with open("dev/article.md", "r") as f:
        article = Article.validate(f.read())
    await parse_links(model, article, lang="中文")
    with open("dev/article_cleaned.md", "w") as f:
        f.write(article.dump_md())


if __name__ == "__main__":
    from dotenv import load_dotenv
    import asyncio

    load_dotenv()
    asyncio.run(main())
