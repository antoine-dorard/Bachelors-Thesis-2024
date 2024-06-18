import networkx as nx
from abc import ABC, abstractmethod
from typing import Union

from parsing.objects import JavaMethod

class Cluster():
    """
    Contains a list of JavaMethod objects that are part of the same cluster.
    """
    def __init__(self, elements: list[JavaMethod]) -> None:
        self.elements: list[JavaMethod] = elements
        self.summary = ""
        
    def add_element(self, element: JavaMethod) -> None:
        self.elements.append(element)
        
    def get_elements(self) -> list[JavaMethod]:
        return self.elements
    
    
class ClusteringInterface(ABC):
    """
    Use this abstract class to implement different clustering algorithms.
    """
    def __init__(self) -> None:
        self.graph: nx.Graph = nx.empty_graph()
        self.clusters: list[Cluster] = []
        self.unique_methods: set[JavaMethod] = set()
        self.params = {}
        
    @abstractmethod
    def cluster(self, java_files, params) -> list[Cluster]:
        """
        Implement this method with the clustering algorithm of your choice. It must populate the self.clusters and 
        self.unique_methods attributes. 
        
        Parameters: 
        - java_files (list[JavaFile]): a list of JavaFile objects that contain all the parsed code.
        - params: additional parameters that can be passed to the clustering algorithm when registering it in the pipeline.
        
        Returns: 
        self.clusters (list[Cluster]): a list of Cluster objects that contain the methods that are part of the same cluster. 
        Each cluster object must contain instances of JavaMethod.
        """
        pass
    
    def get_clusters(self) -> list[Cluster]:
        return self.clusters
    
    def get_unique_methods(self) -> set[JavaMethod]:
        return self.unique_methods
    
    def set_params(self, params: dict) -> None:
        self.params = params
    
        
def convert_louvain_to_clusters(partition: dict[Union[str, JavaMethod], int]) -> list[Cluster]:
    """
    Takes as input the partition dictionary from the Louvain algorithm and converts it to a list of Cluster objects.
    
    Parameters:
    partition (dict[Union[str, JavaMethod], int]): a dictionary that maps JavaMethod objects to cluster IDs
    
    Returns:
    list[Cluster]: a list of Cluster objects
    """
    clusters = []
    communities = set()
    
    for method, community in partition.items():
        communities.add(community)

    for _ in range(len(communities)):
        clusters.append(Cluster([]))
        
    for method, community in partition.items():
        clusters[community].add_element(method)
    
    return clusters


def convert_clusters_to_partition(clusters: list[Cluster]) -> dict:
    """
    Takes as input a list of Cluster objects and converts it to a partition dictionary.
    
    Parameters:
    clusters (list[Cluster]): a list of Cluster objects
    
    Returns:
    dict: a dictionary that maps JavaMethod objects to cluster IDs
    """
    partition = {}
    
    for cluster_id, cluster in enumerate(clusters):
        for method in cluster.get_elements():
            partition[method] = cluster_id
    return partition