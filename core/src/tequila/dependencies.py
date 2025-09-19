from typing import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.settings import ModelSettings
from tequila.storage.space import Space
from opendal import AsyncOperator

# Global variables to store model
_global_model: OpenAIChatModel = None # type: ignore

# Dependency functions
async def get_model() -> OpenAIChatModel:
    return _global_model

async def get_space(space_name: str) -> Space:
    opendal = AsyncOperator(
        "fs",
        root=space_name,
    )
    space = Space(
        name=space_name,
        _opendal=opendal,
        _docs_path="docs",
        _graph_file="graph.pkl",
        _lock_fs_file=f"{space_name}/graph.lock",
    )
    return space

def new_model():
    return OpenAIChatModel(
        model_name="qwen/qwen3-235b-a22b-2507", provider="openrouter",
        # settings=ModelSettings(
        #     temperature=0.8,
        # )
    )
    

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    global _global_model
    _global_model = new_model()
    yield
    # Shutdown (if needed)
