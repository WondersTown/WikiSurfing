from fastapi import FastAPI, HTTPException, Depends
from fastapi.routing import APIRoute
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Union, Literal

from pydantic_ai.models.openai import OpenAIChatModel
from tequila.storage.space import Space

from tequila.pipeline import (
    _gen_article,
    _get_proto_with_context,
    _get_proto_with_related_articles,
)
from tequila.article import ProtoArticle, Article, ProtoOrArticleType
from tequila.dependencies import get_model, get_space, lifespan

from tequila.storage.docs import read_doc


# Pydantic models for response
class ProtoWithContextResponse(BaseModel):
    proto: ProtoOrArticleType
    context: list[str]


class ProtoWithRelatedResponse(BaseModel):
    proto: ProtoOrArticleType
    related_articles: List[Article]


# Pydantic model for generate article request
class GenerateArticleRequest(BaseModel):
    lang: str = "中文"
    context: Union[str, List[str], None, Literal["auto"]] = "auto"
    style_inst: Optional[str] = None
    streaming: Union[float, bool] = False


def generate_unique_id(route: APIRoute):
    return str(route.name)


app = FastAPI(
    title="Tequila Wiki API",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/api",
    generate_unique_id_function=generate_unique_id,
)


@app.get("/")
async def root():
    return {"message": "Tequila Wiki API is running"}


@app.post(
    "/spaces/{space_name}/articles/{title}/generate",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "text/event-stream": {
                    "schema": {"$ref": "#/components/schemas/Article"}
                }
            },
        }
    },
)
async def generate_article(
    title: str,
    request: GenerateArticleRequest,
    model: OpenAIChatModel = Depends(get_model),
    space: Space = Depends(get_space),
):
    """Generate an article based on the provided parameters."""
    proto = ProtoArticle(title=title)
    if request.context == "auto":
        context = await _get_proto_with_context(space=space, title=title)
        if context is None:
            raise HTTPException(status_code=404, detail=f"Article '{title}' not found")
        proto, context = context
    else:
        context = request.context

    async def generate():
        async for article in _gen_article(
            model=model,
            space=space,
            proto=proto,
            lang=request.lang,
            context=context,
            style_inst=request.style_inst,
            streaming=request.streaming,
        ):
            yield f"data: {article.model_dump_json()}\n\n"

    # return EventSourceResponse(generate())
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/spaces/{space_name}/articles/{title}")
async def get_article(title: str, space: Space = Depends(get_space)) -> Article:
    """Get a proto article with context for the given title."""
    # res = await _get_proto_with_context(space=space, title=title)
    doc = await read_doc(space, name=title)
    if isinstance(doc, Article):
        return doc
    elif doc is None:
        raise HTTPException(status_code=404, detail=f"Article '{title}' not found")
    else:
        raise HTTPException(
            status_code=404, detail=f"'{title}' is not a comleted Article"
        )


@app.get("/spaces/{space_name}/articles/{title}/proto")
async def get_article_proto(
    title: str, space: Space = Depends(get_space)
) -> ProtoArticle | Article:
    """Get a proto article with context for the given title."""
    # res = await _get_proto_with_context(space=space, title=title)
    doc = await read_doc(space, name=title)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Article '{title}' not found")
    return doc


@app.get("/spaces/{space_name}/articles/{title}/proto/context")
async def get_article_proto_with_context(
    title: str, space: Space = Depends(get_space)
) -> ProtoWithContextResponse:
    """Get a proto article with context for the given title."""
    res = await _get_proto_with_context(space=space, title=title)
    if res is None:
        raise HTTPException(status_code=404, detail=f"Article '{title}' not found")
    proto, context = res
    return ProtoWithContextResponse(proto=proto, context=context)


@app.get("/spaces/{space_name}/articles/{title}/proto/related")
async def get_article_proto_with_related(
    title: str, space: Space = Depends(get_space)
) -> ProtoWithRelatedResponse:
    """Get a proto article with related articles for the given title."""
    res = await _get_proto_with_related_articles(space=space, title=title)
    if res is None:
        raise HTTPException(status_code=404, detail=f"Article '{title}' not found")
    proto, related_articles = res
    return ProtoWithRelatedResponse(proto=proto, related_articles=related_articles)


schema = app.openapi()
schema["paths"]["/spaces/{space_name}/articles/{title}/generate"]["post"]["responses"][
    "200"
]["content"].pop("application/json")
app.openapi = lambda: schema


if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    import logfire
    import logging

    logfire.configure()
    logfire.instrument_pydantic_ai()
    logfire.instrument_fastapi(app)
    logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
    logging.getLogger("__main__").setLevel(logging.DEBUG)
    logging.getLogger("tequila").setLevel(logging.DEBUG)



    load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8000)
