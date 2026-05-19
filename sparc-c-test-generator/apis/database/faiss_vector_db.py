import json
import pickle
import numpy as np
from typing import Any, Dict, List, Tuple

try:
    import faiss

    FAISS_AVAILABLE = True
    print("FAISS is available.")
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS not available. Install with: pip install faiss-cpu")


class FAISSVectorDB:
    """
    FAISS-based vector database for storing and retrieving function embeddings.
    """

    def __init__(self, embedding_dim: int = 1536):
        """
        Initialize the vector database.

        Args:
            embedding_dim: Dimension of the embeddings (1536 for text-embedding-3-small)
        """
        self.embedding_dim = embedding_dim
        self.index = None
        self.functions = []  # Store function metadata
        self.is_trained = False

        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is required. Install with: pip install faiss-cpu")

    def build_index(
        self, functions_with_embeddings: List[Dict[str, Any]], index_type: str = "flat"
    ) -> None:
        """
        Build FAISS index from functions with embeddings.

        Args:
            functions_with_embeddings: List of function dictionaries with 'embedding' field
            index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')
        """
        # Extract embeddings and metadata
        embeddings = []
        self.functions = []

        for func in functions_with_embeddings:
            if "embedding" in func and func["embedding"]:
                embeddings.append(func["embedding"])
                # Store function without embedding to save memory
                func_copy = {k: v for k, v in func.items() if k != "embedding"}
                self.functions.append(func_copy)

        if not embeddings:
            raise ValueError("No functions with embeddings found")

        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)

        # Create FAISS index based on type
        if index_type == "flat":
            self.index = faiss.IndexFlatL2(
                self.embedding_dim
            )  # Inner product (cosine similarity)
        elif index_type == "ivf":
            # IVF index for larger datasets
            nlist = min(100, len(embeddings) // 10)  # Number of clusters
            quantizer = faiss.IndexFlatIP(self.embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
            self.index.train(embeddings_array)
            self.is_trained = True
        elif index_type == "hnsw":
            # HNSW index for fast approximate search
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_array)

        # Add embeddings to index
        self.index.add(embeddings_array)

        print(
            f"Built FAISS index with {len(embeddings)} functions using {index_type} index"
        )

    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar functions using the vector database.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return

        Returns:
            List of tuples (function_dict, similarity_score)
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Normalize query embedding
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)

        # Search
        similarities, indices = self.index.search(query_array, top_k)

        # Return results
        results = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if idx != -1:  # Valid result
                results.append((self.functions[idx], float(similarity)))

        return results

    def save(self, index_path: str, metadata_path: str) -> None:
        """
        Save the FAISS index and metadata to disk.

        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save function metadata
        """
        if self.index is None:
            raise ValueError("No index to save")

        faiss.write_index(self.index, index_path)

        with open(metadata_path, "wb") as f:
            pickle.dump(
                {
                    "functions": self.functions,
                    "embedding_dim": self.embedding_dim,
                    "is_trained": self.is_trained,
                },
                f,
            )

        print(f"Saved FAISS index to {index_path} and metadata to {metadata_path}")

    def load(self, index_path: str, metadata_path: str) -> None:
        """
        Load FAISS index and metadata from disk.

        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata file
        """
        self.index = faiss.read_index(index_path)

        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
            self.functions = metadata["functions"]
            self.embedding_dim = metadata["embedding_dim"]
            self.is_trained = metadata["is_trained"]

        print(f"Loaded FAISS index with {len(self.functions)} functions")

    @classmethod
    def from_embedded_json(
        cls, json_path: str, index_type: str = "flat"
    ) -> "FAISSVectorDB":
        """
        Create vector database from an embedded JSON file.

        Args:
            json_path: Path to JSON file with embedded functions
            index_type: Type of FAISS index to create

        Returns:
            FAISSVectorDB instance
        """
        # Load embedded JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract functions with embeddings
        functions_with_embeddings = []

        if "all_functions" in data:
            functions_with_embeddings.extend(data["all_functions"])

        if "functions" in data:
            functions_with_embeddings.extend(data["functions"])

        if "source_files" in data:
            for _, functions in data["source_files"].items():
                functions_with_embeddings.extend(functions)

        # Create and build index
        vector_db = cls()
        vector_db.build_index(functions_with_embeddings, index_type)

        return vector_db
