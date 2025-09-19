from networkx import MultiGraph
from opendal import AsyncOperator


import pickle
from contextlib import asynccontextmanager
from io import BytesIO
from typing import AsyncGenerator
from filelock import AsyncUnixFileLock, BaseAsyncFileLock
from dataclasses import dataclass, field


@dataclass(slots=True)
class SpaceRes:
    op: AsyncOperator
    g: "MultiGraph[str]"
    docs_path: str


@dataclass(slots=True, kw_only=True)
class Space:
    name: str
    _opendal: AsyncOperator
    _docs_path: str
    """Reletive to the opendal"""
    _graph_file: str
    """Reletive to the opendal"""
    _lock_fs_file: str
    """Should be a fs path"""
    _lock: BaseAsyncFileLock = field(init=False)

    def __post_init__(self):
        self._lock = AsyncUnixFileLock(self._lock_fs_file, timeout=60)

    async def _read(self) -> "MultiGraph[str]":
        if await self._opendal.exists(self._graph_file):
            f = await self._opendal.read(self._graph_file)
            graph = pickle.load(BytesIO(f))
        else:
            graph = MultiGraph()
        return graph

    async def _write(self, graph: "MultiGraph[str]"):
        await self._opendal.write(self._graph_file, pickle.dumps(graph))

    @asynccontextmanager
    async def mutex(self) -> AsyncGenerator[SpaceRes, None]:
        async with self._lock:
            graph = await self._read()
            try:
                yield SpaceRes(op=self._opendal, g=graph, docs_path=self._docs_path)
            except:
                raise
            else:
                await self._write(graph)
