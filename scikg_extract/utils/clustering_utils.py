from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def cluster_similar_values_dbscan(values: list[str], embedding_model: str, eps: float = 0.2, min_samples: int = 2) -> dict[int, list[str]]:
    """
    Cluster similar values using sentence transformer embeddings and a clustering algorithm.
    Args:
        values (list[str]): List of values to cluster.
        embedding_model (str): The embedding model to use.
        eps (float): Maximum distance between samples in a cluster (lower = stricter).
        min_samples (int): Minimum samples in a cluster.
    Returns:
        dict[int, list[str]]: Dictionary with cluster labels as keys and lists of values as values.
    """

    # Load the sentence transformer model
    model = SentenceTransformer(embedding_model)

    # Generate embeddings for the values
    embeddings = model.encode(values)

    # Compute cosine similarity matrix
    similarity_matrix = cosine_similarity(embeddings)
    
    # Clip similarity values to [0, 1] to avoid floating point errors
    similarity_matrix = np.clip(similarity_matrix, 0, 1)
    
    # Compute distance matrix
    distance_matrix = 1 - similarity_matrix

    # Cluster with DBSCAN
    dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
    labels = dbscan.fit_predict(distance_matrix)

    # Organize values by cluster labels
    clustered_values: dict[int, list[str]] = {}
    for label, value in zip(labels, values):
        if label not in clustered_values:
            clustered_values[label] = []
        clustered_values[label].append(value)

    # Return the clustered values
    return clustered_values