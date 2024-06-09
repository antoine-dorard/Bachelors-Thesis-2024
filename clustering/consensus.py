import numpy as np
from ivc.algorithms import (
    iterative_voting_consensus,
    iterative_probabilistic_voting_consensus,
)

from clustering.clustering import ClusteringInterface, Cluster
from parsing.objects import JavaMethod


def encode_clusterings(clusters: list[Cluster]) -> dict:
    """
    Converts the clsuters list to a dictionary of method -> cluster_id
    """
    encoding = {}
    cluster_id = 0
    for cluster in clusters:
        for method in cluster.get_elements():
            encoding[method] = cluster_id
        cluster_id += 1
    return encoding

def create_cluster_matrix(clustering_results: list[list[Cluster]], all_methods: list[JavaMethod]) -> np.ndarray:
    method_index = {method: idx for idx, method in enumerate(all_methods)}
    cluster_matrix = np.empty((len(all_methods), len(clustering_results)), dtype=int)
    
    for idx, clusters in enumerate(clustering_results):
        encoding = encode_clusterings(clusters)
        for method in all_methods:
            cluster_matrix[method_index[method], idx] = encoding[method]
    
    return cluster_matrix


def decode_clusterings(pi_star: np.ndarray, all_methods: list[JavaMethod]) -> list[Cluster]:
    clusters = {}  # Maps cluster IDs to Cluster objects
    # Initialize Cluster objects for each unique cluster ID
    for cluster_id in np.unique(pi_star):
        clusters[cluster_id] = Cluster([])

    # Assign each JavaMethod to the appropriate Cluster
    for method_idx, cluster_id in enumerate(pi_star):
        #all_methods[method_idx].parent_cluster = clusters[cluster_id]
        clusters[cluster_id].add_element(all_methods[method_idx])

    return list(clusters.values())
