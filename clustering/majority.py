import numpy as np
from ivc.algorithms import (
    iterative_voting_consensus,
    iterative_probabilistic_voting_consensus,
)

from clustering.clustering import ClusteringInterface, Cluster
from parsing.objects import JavaMethod

def majority(cluster1: ClusteringInterface, cluster2: ClusteringInterface) -> ClusteringInterface:
    """
    Combine the results of two clustering algorithms using a majority voting system.
    """
    pass

    
def check_cluster(groundtruth: np.ndarray, found: np.ndarray) -> float:
    """Evaluate the percentage of errors between the groundtruth clustering and the found clustering.

    Parameters
    ----------
    groundtruth : np.ndarray
        Groundtruth clustering
    found : np.ndarray
        Estimated clustering

    Returns
    -------
    float
        Percentage of error
    """
    values = np.unique(groundtruth)
    errors = 0
    for value in values:
        mask = groundtruth == value
        counts = np.bincount(found[mask])
        errors += counts.sum() - counts.max()
    return errors / groundtruth.size

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
        all_methods[method_idx].parent_cluster = clusters[cluster_id]
        clusters[cluster_id].add_element(all_methods[method_idx])

    return list(clusters.values())



def test_run():
    """
    temporary test function to run the majority function
    """
    # Parameters
    number_of_clusters = 10
    number_of_clusterings = 5

    # Generate the true clusterings
    clusters_true = np.random.randint(number_of_clusters, size=(1000))
    print(clusters_true.shape)

    # Simulate various corrupted clusterings
    clusters_false = np.repeat(
        clusters_true[:, None], repeats=number_of_clusterings, axis=1
    )
    replacements = np.random.randint(number_of_clusters, size=clusters_false.shape)
    mask = np.random.choice([0, 1], size=clusters_false.shape, p=[0.9, 0.1]).astype(
        np.bool_
    )
    clusters_false[mask] = replacements[mask]
    print(clusters_false.shape)

    # Use the algorithms to find the true clusterings
    pi_star = iterative_voting_consensus(clusters_false, max_value=number_of_clusters)
    print(pi_star.shape)
    print(
        f"Percentage of error with the IVC algorithm {check_cluster(clusters_true, pi_star)}"
    )

    pi_star = iterative_probabilistic_voting_consensus(
        clusters_false, max_value=number_of_clusters
    )
    print(
        f"Percentage of error with the IPVC algorithm {check_cluster(clusters_true, pi_star)}"
    )
    