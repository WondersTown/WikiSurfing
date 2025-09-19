from tequila.article import ProtoArticle, Article
import networkx as nx

from tequila.parse_links import parse_links
from pydantic_ai.models import Model
from tequila.storage.space import Space
from tequila.storage.docs import upsert_doc, read_doc
from tequila.dependencies import get_space, new_model
from tequila.utils import replace_text_with_links
from tequila.article import (
    write_article,
)
import logging
logger = logging.getLogger(__name__)


async def _gen_article(
    model: Model,
    space: Space,
    proto: ProtoArticle,
    *,
    lang: str,
    context: str | list[str] | None = None,
    style_inst: str | None = None,
    streaming: float | bool = False,
):
    if isinstance(context, list):
        context = "\n".join(context)
    async for article in write_article(
        model, proto, lang, context=context, style_inst=style_inst, streaming=streaming
    ):
        yield article
    yield article
    await parse_links(model, article, lang)
    yield article
    await upsert_doc(space, article)


async def _get_proto_with_related_articles(
    space: Space,
    title: str,
    *,
    alpha: float = 0.85,
    top_k: int = 10,
):
    # Get the article content
    article = await read_doc(space, title)
    if article is None:
        return None

    # Get directly connected nodes (neighbors) of the title
    async with space.mutex() as res:
        undirected = nx.Graph(res.g)

    ppr_dict = {node: 0 for node in undirected.nodes()}
    ppr_dict[title] = 1
    ppr_scores = nx.pagerank(undirected, alpha=alpha, personalization=ppr_dict)
    sorted_ppr = sorted(ppr_scores.items(), key=lambda item: item[1], reverse=True)

    connected_articles: list[Article] = []
    # Read articles for each connected node
    for node_title, _score in sorted_ppr:
        node_article = await read_doc(space, node_title)
        if node_article is None:
            logger.warning(f"Article {node_title} not found in space {space.name}")
            continue
        if node_article.title == title:
            continue
        if node_article.kind == "article":
            connected_articles.append(node_article)
        if len(connected_articles) >= top_k:
            break
    logger.info(f"Connected articles: {[x.title for x in connected_articles]}")


    return article, connected_articles


async def _get_proto_with_context(
    space: Space,
    title: str,
):
    res = await _get_proto_with_related_articles(
        space,
        title,
    )
    if res is None:
        return None
    proto, related = res
    related_texts = [
        "<RelatedArticle>"
        + replace_text_with_links(x.content, set(x.links.keys()))
        + "</RelatedArticle>\n"
        for x in related
    ]
    return proto, related_texts


async def prepare(space_name: str):
    import logfire

    logfire.configure()
    logfire.instrument_pydantic_ai()
    logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
    logging.getLogger("__main__").setLevel(logging.DEBUG)
    logging.getLogger("tequila").setLevel(logging.DEBUG)


    model = new_model()
    space = await get_space(space_name)
    return model, space


async def gen_article_pipeline():
    from rich.live import Live
    from rich.text import Text
    from rich.panel import Panel

    model, space = await prepare("default")

    with Live(
        Text("Starting..."), refresh_per_second=10, vertical_overflow="crop"
    ) as live:
        res = await _get_proto_with_context(space=space, title="黑林村")
        if res is None:
            proto, context = ProtoArticle(title="黑林村瘟疫"), "(1348-1351)"
        else:
            proto, context = res
        async for part in _gen_article(
            model,
            space,
            proto,
            lang="中文",
            context=context,
            style_inst="中世纪欧洲风格，注意地名不能叫做'欧洲'",
            streaming=True,
        ):
            # Create a panel with the current content
            content = Panel(
                part.content,
                title="Output",
                title_align="left",
                border_style="blue",
            )
            live.update(content)


if __name__ == "__main__":
    from dotenv import load_dotenv
    import asyncio

    load_dotenv()
    asyncio.run(gen_article_pipeline())
