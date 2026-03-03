from typing import List, Dict, Any, Optional
from chromadb import Client, Settings
from chromadb.config import Settings as ChromaSettings
import hashlib
from datetime import datetime


class VectorMemory:
    """Memoria vectorial para contexto semántico"""

    def __init__(self, project_id: str, chroma_url: str = "http://localhost:8000"):
        self.project_id = project_id
        self.collection_name = f"project_{project_id}"

        # Conectar a ChromaDB
        self.client = Client(
            settings=ChromaSettings(
                chroma_api_impl="rest",
                chroma_server_host=chroma_url.split("//")[1].split(":")[0],
                chroma_server_http_port=chroma_url.split(":")[-1]
            )
        )

        # Obtener o crear colección
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"project_id": project_id}
        )

        # Inicializar embeddings con Ollama
        from langchain_ollama import OllamaEmbeddings
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )

    def store(self, content: str, metadata: Dict[str, Any] = None,
              category: str = "general") -> str:
        """Almacena contenido en memoria vectorial"""
        doc_id = self._generate_id(content, metadata)

        # Generar embedding
        embedding = self.embeddings.embed_query(content)

        # Preparar metadata
        full_metadata = {
            **(metadata or {}),
            'project_id': self.project_id,
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'doc_id': doc_id
        }

        # Guardar en ChromaDB
        self.collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[full_metadata]
        )

        return doc_id

    def retrieve(self, query: str, categories: List[str] = None,
                 limit: int = 10) -> List[Dict[str, Any]]:
        """Recupera contenido relevante"""
        # Generar embedding de query
        query_embedding = self.embeddings.embed_query(query)

        # Preparar filtro
        where_filter = {"project_id": self.project_id}
        if categories:
            where_filter["category"] = {"$in": categories}

        # Buscar
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        # Formatear resultados
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None
                })

        return formatted

    def store_code_snapshot(self, file_path: str, content: str,
                            commit_hash: str = None) -> str:
        """Guarda snapshot de código"""
        return self.store(
            content=content,
            metadata={
                'file_path': file_path,
                'commit': commit_hash,
                'type': 'code'
            },
            category='codebase'
        )

    def store_decision(self, decision: Dict[str, Any]) -> str:
        """Guarda decisión arquitectónica"""
        content = f"{decision['title']}: {decision['decision']}"
        return self.store(
            content=content,
            metadata={**decision, 'type': 'decision'},
            category='decisions'
        )

    def clear(self):
        """Limpia toda la memoria del proyecto"""
        self.client.delete_collection(self.collection_name)

    def _generate_id(self, content: str, metadata: Dict = None) -> str:
        """Genera ID único para documento"""
        seed = f"{self.project_id}:{content[:100]}:{metadata or ''}"
        return hashlib.md5(seed.encode()).hexdigest()