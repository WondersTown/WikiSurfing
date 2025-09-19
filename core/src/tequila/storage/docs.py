"""
Document storage module for the Tequila wiki system.

This module provides functionality for reading, writing, and managing wiki articles
and their relationships using both file storage (via OpenDAL) and graph storage
(via NetworkX MultiGraph). It handles both full articles and proto-articles (placeholders).

The module supports:
- Reading documents from storage with graph validation
- Writing documents to storage with automatic link management
- Upserting documents with conflict resolution and cleanup
- Managing graph relationships between articles
"""

from opendal import AsyncOperator
from opendal.exceptions import NotFound

from networkx import MultiGraph

from pathlib import Path
from tequila.article import (
    proto_or_article_adapter,
    ProtoOrArticleType,
    Article,
    ProtoArticle,
)
from tequila.storage.space import Space


async def _read_doc(
    opendal: AsyncOperator,
    g: "MultiGraph[str] ",
    name: str,
    *,
    path: str,
):
    """
    Internal function to read a document from storage.

    This function checks if the document exists in the graph before attempting
    to read it from storage, ensuring consistency between graph and file storage.

    Args:
        opendal: Async operator for file operations
        g: NetworkX MultiGraph containing document relationships
        name: Name/title of the document to read
        path: Storage path for documents (default: "docs")

    Returns:
        ProtoOrArticleType: The document if found, None otherwise

    Note:
        This is an internal function that requires an already-opened graph.
        Use read_doc() for external calls.
    """
    if g.has_node(name):
        # Read the JSON file from storage
        try:
            text = await opendal.read(Path(path) / (name + ".json"))
        except NotFound:
            return None
        return proto_or_article_adapter.validate_json(text)
    else:
        return None


async def read_doc(
    graph: Space,
    name: str,
):
    """
    Read a document from storage.

    Public interface for reading documents that handles graph opening/closing
    automatically. Only returns documents that exist in both the graph and
    file storage.

    Args:
        opendal: Async operator for file operations
        graph: Graph handler for managing document relationships
        name: Name/title of the document to read
        path: Storage path for documents (default: "docs")

    Returns:
        ProtoOrArticleType: The document if found, None otherwise
    """
    async with graph.mutex() as res:
        return await _read_doc(res.op, res.g, name, path=res.docs_path)


async def _write_doc(
    opendal: AsyncOperator,
    g: "MultiGraph[str]",
    content: ProtoOrArticleType,
    *,
    path: str,
    write_graph: bool = True,
):
    """
    Internal function to write a document to storage.

    Handles both file storage and graph updates. For Article objects,
    automatically creates proto-articles for linked documents and
    establishes graph relationships.

    Args:
        opendal: Async operator for file operations
        g: NetworkX MultiGraph for relationships (required if write_graph=True)
        content: Document content to write (Article or ProtoArticle)
        path: Storage path for documents (default: "docs")
        write_graph: Whether to update the graph with this document

    Raises:
        ValueError: If write_graph=True but g is None

    Note:
        This is an internal function. Use write_doc() for external calls.
    """
    if write_graph:
        # Add the document as a node in the graph
        g.add_node(content.title)

        # If it's a full article, process its links
        if isinstance(content, Article):
            for href, alters in content.links.items():
                # Create or update proto-articles for linked documents
                await _upsert_doc(
                    opendal,
                    g,
                    ProtoArticle(title=href, alt_title=alters),
                    path=path,
                )
                # Create an edge from this article to the linked article
                g.add_edge(content.title, href, key=content.title)

    # Write the document to file storage as JSON
    await opendal.write(
        Path(path) / (content.title + ".json"),
        content.model_dump_json().encode("utf-8"),
    )


async def write_doc(
    graph: Space,
    content: ProtoOrArticleType,
    *,
    write_graph: bool = True,
):
    """
    Write a document to storage.

    Public interface for writing documents that handles graph opening/closing
    automatically. Supports both full articles and proto-articles.

    Args:
        opendal: Async operator for file operations
        graph: Graph handler for managing document relationships
        content: Document content to write (Article or ProtoArticle)
        path: Storage path for documents (default: "docs")
        write_graph: Whether to update the graph with this document

    Note:
        When writing full articles, this function automatically creates
        proto-articles for any linked documents that don't exist yet.
    """
    async with graph.mutex() as res:
        await _write_doc(
            res.op, res.g, content, path=res.docs_path, write_graph=write_graph
        )


async def _upsert_doc(
    opendal: AsyncOperator,
    g: "MultiGraph[str]",
    content: ProtoOrArticleType,
    *,
    path: str,
):
    """
    Internal function to upsert (insert or update) a document.

    Implements sophisticated conflict resolution logic:
    - If document doesn't exist: create it
    - If existing proto-article + new proto-article: merge alt_titles
    - If existing proto-article + new article: replace with article
    - If existing article + new proto-article: keep existing article
    - If existing article + new article: replace and clean up old links

    Args:
        opendal: Async operator for file operations
        g: NetworkX MultiGraph for managing relationships
        content: Document content to upsert
        path: Storage path for documents (default: "docs")

    Note:
        This function handles complex cleanup when replacing articles,
        including removing orphaned proto-articles that are no longer linked.
    """
    # Check if document already exists
    readed = await _read_doc(opendal, g, content.title, path=path)

    if readed is None:
        # Document doesn't exist, create it
        await _write_doc(opendal, g, content, path=path)
    elif readed.kind == "proto_article":
        # Existing document is a proto-article
        if content.kind == "proto_article":
            # Both are proto-articles: merge alternative titles
            readed.alt_title.update(content.alt_title)
            await _write_doc(opendal, g, readed, path=path, write_graph=False)
        else:
            # New content is a full article: replace proto-article
            await _write_doc(opendal, g, content, path=path)
    else:
        # Existing document is a full article
        if content.kind == "proto_article":
            # New content is proto-article: keep existing full article
            pass
        else:
            # Both are full articles: replace and clean up old links

            # Find all documents that this article links to
            links = [
                target
                for source, target, key in g.edges(readed.title, keys=True)
                if key == readed.title
            ]

            # Clean up old links
            for link in links:
                link_doc = await _read_doc(opendal, g, link, path=path)
                if link_doc is None:
                    continue

                # Remove the edge from old article to this link
                g.remove_edge(readed.title, link, key=readed.title)

                # If the linked document is a proto-article with no remaining links
                if link_doc.kind == "proto_article":
                    # Check if the link node has no incoming edges
                    if len(list(g.edges(link))) == 0:
                        # Delete the orphaned proto-article from graph and storage
                        g.remove_node(link)
                        await opendal.delete(Path(path) / (link + ".json"))

            # Write the new article (which will create new links)
            await _write_doc(opendal, g, content, path=path)


async def upsert_doc(
    graph: Space,
    content: ProtoOrArticleType,
):
    """
    Upsert (insert or update) a document in storage.

    Public interface for upserting documents that handles graph opening/closing
    automatically. Provides intelligent conflict resolution between different
    document types and automatic cleanup of orphaned references.

    Args:
        opendal: Async operator for file operations
        graph: Graph handler for managing document relationships
        content: Document content to upsert (Article or ProtoArticle)
        path: Storage path for documents (default: "docs")

    Note:
        This is the recommended way to save documents as it handles all
        edge cases and maintains consistency between articles and their links.
    """
    async with graph.mutex() as res:
        await _upsert_doc(res.op, res.g, content, path=res.docs_path)
