import os
from typing import List, Dict, Any
from apis.database.faiss_vector_db import FAISSVectorDB

from apis.gpt import GPT_Connection


class VectorDBManager:
    def __init__(self):
        self.gpt_connection = GPT_Connection()
        self.vector_db = None

    def init_vector_db(
        self,
        embedded_json_path: str,
        index_type: str = "flat",
        save_index: bool = True,
        index_dir: str = "database",
    ) -> None:
        """
        Initialize FAISS vector database from embedded JSON.

        Args:
            embedded_json_path: Path to JSON file with embeddings
            index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')
            save_index: Whether to save the index to disk
            index_dir: Directory to save index files
        """
        self.vector_db = FAISSVectorDB.from_embedded_json(
            embedded_json_path, index_type
        )

        if save_index:
            os.makedirs(index_dir, exist_ok=True)
            index_path = os.path.join(index_dir, "faiss.index")
            metadata_path = os.path.join(index_dir, "metadata.pkl")
            self.vector_db.save(index_path, metadata_path)

    def load_vector_db(self, index_dir: str = "database") -> None:
        """
        Load FAISS vector database from disk.

        Args:
            index_dir: Directory containing index files
        """
        index_path = os.path.join(index_dir, "faiss.index")
        metadata_path = os.path.join(index_dir, "metadata.pkl")

        self.vector_db = FAISSVectorDB(embedding_dim=1536)
        self.vector_db.load(index_path, metadata_path)

    def get_vector_db(self) -> FAISSVectorDB:
        """
        Get the FAISS vector database instance.

        Returns:
            FAISSVectorDB instance
        """
        return self.vector_db

    def get_all_functions(self) -> List[Dict[str, Any]]:
        """
        Get all functions from the vector database.

        Returns:
            List of all function dictionaries
        """
        if self.vector_db is None:
            raise ValueError(
                "Vector database not initialized. Call init_vector_db() or load_vector_db() first."
            )

        return self.vector_db.functions
