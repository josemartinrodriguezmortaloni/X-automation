from pathlib import Path
from agno.knowledge.document import (
    DocumentKnowledgeBase as _BaseKnowledgeBase,
    Document as _BaseDocument,
)
from agno.vectordb.chroma import ChromaDb
import logging

logger = logging.getLogger(__name__)


class Document(_BaseDocument):
    """
    Document subclass with metadata support.
    """

    def __init__(self, content: str, metadata: dict):
        super().__init__(content)
        # Store metadata override and assign to __dict__ for compatibility
        self._metadata_override = metadata
        self.__dict__["metadata"] = metadata

    @property
    def metadata(self) -> dict:
        # Return metadata for indexing
        return self._metadata_override


class Knowledge:
    # Directory containing source documents to index
    docs_dir = Path(__file__).parent.parent / "docs"
    # Discover markdown files and log their names
    _md_paths = list(docs_dir.glob("*.md"))
    logger.info(
        f"Knowledge base initializing with {len(_md_paths)} documents: {[p.name for p in _md_paths]}"
    )
    # Build Document subclass instances with metadata
    documents = [
        Document(path.read_text(encoding="utf-8"), metadata={"source": path.name})
        for path in _md_paths
    ]
    # Configure ChromaDB vector store
    vector_db = ChromaDb(
        collection="documents",
        path="src/db/knowledge",
        persistent_client=True,
    )
    # Instantiate the knowledge base with documents and vector store
    knowledge_base = _BaseKnowledgeBase(
        documents=documents,
        vector_db=vector_db,
    )
