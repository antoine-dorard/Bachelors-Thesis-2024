import networkx as nx
from abc import ABC, abstractmethod
from typing import Union

from parsing.objects import JavaMethod

class Cluster():
    def __init__(self, elements: list[JavaMethod]) -> None:
        self.elements: list[JavaMethod] = []
        
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
        
    @abstractmethod
    def cluster(self, **kwargs) -> list[Cluster]:
        """
        TODO write comment about the fact that in the pipeline the input includes a list of JavaFile objects.
        """
        pass
    
    def get_clusters(self) -> list[Cluster]:
        return self.clusters
    
        
def convert_louvain_to_clusters(partition: dict[Union[str, JavaMethod], int]) -> list[Cluster]:
    """
    Takes as input the partition dictionary from the Louvain algorithm and converts it to a list of Cluster objects.
    """
    clusters = []
    
    partition = {k: v for k, v in sorted(partition.items(), key=lambda item: item[1])} # Sort the partition by community
    
    previous_community = partition[list(partition.keys())[0]] # get the first community
    current_cluster = Cluster([])
    
    for method, community in partition.items():
        if previous_community == community:
            current_cluster.add_element(method)
        else:
            clusters.append(current_cluster)
            current_cluster = Cluster([])
            
        previous_community = community
        
    clusters.append(current_cluster)
    
    return clusters
