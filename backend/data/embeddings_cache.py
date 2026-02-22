"""
FAISS Vector Database Integration

Handles embedding initialization, FAISS index creation, and similarity search
for OEM product datasheet retrieval. Uses sentence-transformers for embeddings.
"""

import pickle
import os
from typing import List, Tuple, Dict, Any
import numpy as np

from backend.config import settings
from backend.data.models import OEM_PRODUCTS, create_product_embedding_text

# Try importing FAISS and sentence transformers
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("WARNING: FAISS not installed. Will use fallback fuzzy matching.")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("WARNING: sentence-transformers not installed. Vector search disabled.")


class FAISSVectorDB:
    """
    FAISS-based vector database for product similarity search.

    Attributes:
        index: FAISS index object
        embeddings: Precomputed embeddings for OEM products
        products: Product metadata indexed by position
        embed_model: SentenceTransformer model
    """

    def __init__(self):
        """Initialize FAISS index or load from cache."""
        self.index = None
        self.embeddings = None
        self.products = OEM_PRODUCTS
        self.embed_model = None
        self._is_ready = False

        if FAISS_AVAILABLE and EMBEDDINGS_AVAILABLE:
            self._initialize()
        else:
            print("FAISS or embeddings model unavailable. Falling back to keyword matching.")

    def _initialize(self):
        """Initialize embeddings and build FAISS index."""
        try:
            # Load embedding model
            self.embed_model = SentenceTransformer(settings.EMBEDDINGS_MODEL)

            # Try loading cached index
            if os.path.exists(settings.FAISS_INDEX_PATH):
                self._load_from_cache()
                return

            # Build index from scratch
            self._build_index()

        except Exception as e:
            print(f"ERROR initializing FAISS: {e}")
            self._is_ready = False

    def _build_index(self):
        """Build FAISS index from OEM products."""
        try:
            # Create embeddings for all products
            texts = [create_product_embedding_text(p) for p in self.products]
            self.embeddings = self.embed_model.encode(texts)

            # Create FAISS index
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)  # L2 distance
            self.index.add(np.array(self.embeddings, dtype=np.float32))

            # Save to cache
            self._save_to_cache()
            self._is_ready = True

        except Exception as e:
            print(f"ERROR building FAISS index: {e}")
            self._is_ready = False

    def _save_to_cache(self):
        """Save FAISS index and embeddings to disk."""
        try:
            os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
            with open(settings.FAISS_INDEX_PATH, "wb") as f:
                pickle.dump(
                    {
                        "index": self.index,
                        "embeddings": self.embeddings,
                        "products": self.products,
                    },
                    f,
                )
            print(f"FAISS index saved to {settings.FAISS_INDEX_PATH}")
        except Exception as e:
            print(f"WARNING: Could not save FAISS cache: {e}")

    def _load_from_cache(self):
        """Load FAISS index and embeddings from disk."""
        try:
            with open(settings.FAISS_INDEX_PATH, "rb") as f:
                cache = pickle.load(f)
            self.index = cache["index"]
            self.embeddings = cache["embeddings"]
            self.products = cache["products"]
            self._is_ready = True
            print(f"FAISS index loaded from cache: {settings.FAISS_INDEX_PATH}")
        except Exception as e:
            print(f"WARNING: Could not load FAISS cache: {e}. Building from scratch.")
            self._build_index()

    def search(
        self, query_text: str, k: int = None, threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar products using FAISS.

        Args:
            query_text: Query text (product specs in natural language)
            k: Number of results to return (default from settings)
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of matched products with similarity scores, sorted by relevance
        """
        if not self._is_ready or self.embed_model is None:
            return []

        k = k or settings.K_NEAREST_NEIGHBORS
        threshold = threshold or settings.SIMILARITY_THRESHOLD

        try:
            # Embed query
            query_embedding = self.embed_model.encode([query_text])[0]
            query_embedding = np.array([query_embedding], dtype=np.float32)

            # Search FAISS
            distances, indices = self.index.search(query_embedding, min(k, len(self.products)))

            # Convert distances to similarity scores (lower distance = higher similarity)
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                # L2 distance: normalize to 0-1 similarity (1 = identical)
                similarity = 1.0 / (1.0 + distance)

                if similarity >= threshold:
                    product = self.products[idx]
                    results.append(
                        {
                            "sku": product["SKU"],
                            "similarity": float(similarity),
                            "product": product,
                            "match_reason": f"Similarity match: {similarity:.1%}",
                        }
                    )

            return results

        except Exception as e:
            print(f"ERROR in FAISS search: {e}")
            return []


class FuzzyMatcher:
    """
    Fallback fuzzy matching for product search when FAISS is unavailable.

    Uses keyword and attribute matching instead of semantic similarity.
    """

    @staticmethod
    def match_products(
        req_material: str,
        req_insulation: str,
        req_cores: int,
        req_size_mm2: int,
        req_voltage_kv: float,
    ) -> List[Dict[str, Any]]:
        """
        Find matching products using fuzzy attribute matching.

        Args:
            req_material: Required material
            req_insulation: Required insulation
            req_cores: Required cores
            req_size_mm2: Required size
            req_voltage_kv: Required voltage

        Returns:
            List of products ranked by match score
        """
        scores = []

        for product in OEM_PRODUCTS:
            score = 0.0
            reasons = []

            # Material match (weight: 30%)
            if product["Material"] == req_material:
                score += 30.0
                reasons.append("Material match")

            # Insulation match (weight: 20%)
            if product["Insulation"] == req_insulation:
                score += 20.0
                reasons.append("Insulation match")

            # Cores match (weight: 25%)
            if product["Cores"] == req_cores:
                score += 25.0
                reasons.append("Cores match")

            # Size match - meet or exceed (weight: 25%)
            if product["Size_mm2"] >= req_size_mm2:
                size_ratio = min(1.0, product["Size_mm2"] / req_size_mm2)
                score += 25.0 * size_ratio
                reasons.append(f"Size sufficient ({product['Size_mm2']}mm² >= {req_size_mm2}mm²)")

            # Voltage match (bonus)
            if product["Voltage_kV"] == req_voltage_kv:
                score += 5.0
                reasons.append("Voltage match")

            scores.append(
                {
                    "sku": product["SKU"],
                    "similarity": score,  # Percentage match
                    "product": product,
                    "match_reason": " | ".join(reasons),
                }
            )

        # Sort by score descending
        scores.sort(key=lambda x: x["similarity"], reverse=True)
        return scores


# ==================== GLOBAL VECTOR DB INSTANCE ====================
vector_db = FAISSVectorDB()


def search_vector_db(
    query_text: str = None,
    req_material: str = None,
    req_insulation: str = None,
    req_cores: int = None,
    req_size_mm2: int = None,
    req_voltage_kv: float = None,
    k: int = None,
) -> List[Dict[str, Any]]:
    """
    Search for similar products.

    Can be called with either:
    1. query_text: Natural language query
    2. Specification attributes: req_material, req_insulation, etc.

    Args:
        query_text: Natural language query
        req_material: Material requirement
        req_insulation: Insulation requirement
        req_cores: Core count requirement
        req_size_mm2: Size requirement
        req_voltage_kv: Voltage requirement
        k: Number of results

    Returns:
        List of matching products with similarity scores
    """
    # If specifications provided, use fuzzy matcher
    if req_material is not None:
        return FuzzyMatcher.match_products(
            req_material=req_material,
            req_insulation=req_insulation,
            req_cores=req_cores,
            req_size_mm2=req_size_mm2,
            req_voltage_kv=req_voltage_kv,
        )

    # If query text provided and FAISS available, use semantic search
    if query_text and vector_db._is_ready:
        return vector_db.search(query_text, k=k)

    # Fallback: empty result
    return []


# ==================== EXPORT ====================
__all__ = [
    "FAISSVectorDB",
    "FuzzyMatcher",
    "vector_db",
    "search_vector_db",
]
