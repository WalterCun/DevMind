# devmind-core/core/memory/vector_store.py
"""Vector memory compatible with ChromaDB 1.1.1+"""
import hashlib
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_ollama import OllamaEmbeddings

# ✅ ChromaDB 1.1.1 compatible imports
try:
    from chromadb import PersistentClient
except ImportError:
    raise ImportError("Install chromadb>=1.0.0: uv pip install 'chromadb>=1.0.0'")

logger = logging.getLogger(__name__)


class MemoryCategory(str, Enum):
    CODE = "code"
    DECISIONS = "decisions"
    CONVERSATIONS = "conversations"
    REQUIREMENTS = "requirements"
    DOCUMENTATION = "documentation"
    BUGS = "bugs"
    TOOLS = "tools"
    GENERAL = "general"


class VectorMemory:
    DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
    DEFAULT_OLLAMA_URL = "http://localhost:11434"

    def __init__(self, project_id: str, chroma_url: str = None,
                 ollama_url: str = None, embedding_model: str = None,
                 persist_directory: str = None):
        self.project_id = project_id
        self.collection_name = f"devmind_{project_id}"
        self.ollama_url = ollama_url or self.DEFAULT_OLLAMA_URL
        self.embedding_model = embedding_model or self.DEFAULT_EMBEDDING_MODEL
        self._embeddings = OllamaEmbeddings(model=self.embedding_model, base_url=self.ollama_url)
        self._client = self._init_chroma_client(persist_directory)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"project_id": self.project_id, "created_at": datetime.now().isoformat(),
                      "embedding_model": self.embedding_model}
        )
        logger.info(f"VectorMemory initialized for project {project_id}")

    def _init_chroma_client(self, persist_directory: str = None):
        """✅ ChromaDB 1.1.1 compatible: use PersistentClient"""
        persist_dir = Path(persist_directory) if persist_directory else (
                Path.home() / ".devmind" / "chroma_db" / self.project_id)
        persist_dir.mkdir(parents=True, exist_ok=True)
        return PersistentClient(path=str(persist_dir))

    def store(self, content: str, metadata: Dict[str, Any] = None,
              category: MemoryCategory = MemoryCategory.GENERAL, doc_id: str = None) -> str:
        if doc_id is None:
            doc_id = f"{category.value}_{hashlib.md5(f'{self.project_id}:{content[:200]}'.encode()).hexdigest()}"
        full_metadata = {**(metadata or {}), "project_id": self.project_id, "category": category.value,
                         "doc_id": doc_id, "content_length": len(content), "stored_at": datetime.now().isoformat()}
        embedding = self._embeddings.embed_query(content)
        self._collection.upsert(ids=[doc_id], embeddings=[embedding], documents=[content], metadatas=[full_metadata])
        return doc_id

    def retrieve(self, query: str, categories: Optional[List[MemoryCategory]] = None,
                 limit: int = 10, min_similarity: float = 0.0, metadata_filter: Dict[str, Any] = None) -> List[
        Dict[str, Any]]:
        where_filter = {"project_id": self.project_id}
        if categories:
            where_filter["category"] = {"$in": [c.value for c in categories]}
        if metadata_filter:
            where_filter.update(metadata_filter)
        try:
            query_embedding = self._embeddings.embed_query(query)
            results = self._collection.query(query_embeddings=[query_embedding], n_results=limit,
                                             where=where_filter, include=["documents", "metadatas", "distances"])
            formatted = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1 - (distance / 2)
                    if similarity >= min_similarity:
                        formatted.append({"content": doc, "metadata": results["metadatas"][0][i],
                                          "similarity": round(similarity, 4),
                                          "category": results["metadatas"][0][i].get("category")})
            formatted.sort(key=lambda x: x["similarity"], reverse=True)
            return formatted
        except:
            return []

    def store_conversation(self, user_message: str, agent_response: str, intent: str = None,
                           task_id: str = None) -> str:
        return self.store(content=f"User: {user_message}\n\nAgent: {agent_response}",
                          metadata={"user_message": user_message, "agent_response": agent_response,
                                    "intent": intent, "task_id": task_id, "type": "conversation_turn"},
                          category=MemoryCategory.CONVERSATIONS)

    def get_project_knowledge(self, query: str, include_categories: Optional[List[MemoryCategory]] = None) -> str:
        results = self.retrieve(query=query, categories=include_categories, limit=15, min_similarity=0.3)
        if not results:
            return ""
        by_category: Dict[str, List[str]] = {}
        for r in results:
            cat = r["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f"- {r['content'][:300]}...")
        context_parts = []
        for category, items in by_category.items():
            context_parts.append(f"\n## {category.upper()}")
            context_parts.extend(items[:5])
        return "\n".join(context_parts)

    def get_stats(self) -> Dict[str, Any]:
        try:
            count = self._collection.count()
            categories = {}
            for cat in MemoryCategory:
                results = self._collection.get(where={"category": cat.value}, include=["metadatas"])
                if results and results["ids"]:
                    categories[cat.value] = len(results["ids"])
            return {"project_id": self.project_id, "total_documents": count, "by_category": categories,
                    "embedding_model": self.embedding_model, "collection_name": self.collection_name}
        except:
            return {"error": "Failed to get stats"}

    def __repr__(self) -> str:
        return f"VectorMemory(project={self.project_id}, collection={self.collection_name})"