import sys
import os
import pytest
from pathlib import Path

# Ensure the src directory is on PYTHONPATH so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.knowledge import Knowledge


def test_docs_directory_exists_and_has_files():
    """
    Ensure the docs directory exists and contains at least one markdown or text file.
    """
    base_dir = Path(__file__).parent.parent
    docs_dir = base_dir / "docs"
    assert docs_dir.exists(), f"Documentation directory not found at {docs_dir}"
    files = [
        p for p in docs_dir.rglob("*") if p.is_file() and p.suffix in (".md", ".txt")
    ]
    assert files, f"No .md or .txt files found in {docs_dir}"


def test_chromadb_collection_populated():
    """
    Load the knowledge base and verify the ChromaDB 'documents' collection contains items.
    """
    # Load or recreate the chroma collection
    Knowledge.knowledge_base.load(recreate=True)
    # Access the ChromaDB client
    vector_db = Knowledge.knowledge_base.vector_db
    client = getattr(vector_db, "client", getattr(vector_db, "_client", None))
    assert client is not None, "Unable to access underlying ChromaDB client"
    # Retrieve the 'documents' collection
    collection = client.get_collection("documents")
    # Assert the collection has at least one entry
    count = collection.count()
    assert count > 0, (
        f"Expected at least one document in 'documents' collection, found {count}"
    )
