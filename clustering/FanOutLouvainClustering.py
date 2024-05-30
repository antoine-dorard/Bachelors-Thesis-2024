import networkx as nx
import community as community_louvain

from parsing.objects import JavaMethod, JavaFile
from parsing.parsing import parse_method_calls_REGEX
from utils import visualize_community_graph
from .clustering import ClusteringInterface, Cluster, convert_louvain_to_clusters

           
class FanOutClustering(ClusteringInterface):
    def __init__(self) -> None:
        super().__init__()
        
    def cluster(self, file_objects_list: list[JavaFile]) -> list[Cluster]:
         # Cluster the files based on the method calls
    
        self.graph = nx.Graph()
        
        for file1 in file_objects_list:
            for java_class1 in file1.classes:
                for method1 in java_class1.methods:
                    
                    parsed_calls = parse_method_calls_REGEX(method1.code)
                    
                    for file2 in file_objects_list:
                        for java_class2 in file2.classes:
                            for method2 in java_class2.methods:
                                if method1 == method2:
                                    continue
                                
                                if not self.graph.has_edge(method1, method2):
                                    self.graph.add_edge(method1, method2)
                                    self.graph[method1][method2]["calls"] = 0
                                
                                if method2.name in parsed_calls:
                                    count = parsed_calls.count(method2.name)
                                    self.graph[method1][method2]["calls"] += count
        
        for edge in self.graph.edges():
            if self.graph[edge[0]][edge[1]]['calls'] <= 0:
                self.graph.remove_edge(edge[0], edge[1])
                
        partition = community_louvain.best_partition(self.graph.to_undirected())

        # Visualize the communities
        visualize_community_graph(self.graph, partition, "out/fanout_graph.png")
            
        self.clusters = convert_louvain_to_clusters(partition)
        
        return self.clusters