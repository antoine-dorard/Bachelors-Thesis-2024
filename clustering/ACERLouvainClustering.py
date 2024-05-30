import os
import networkx as nx
import community as community_louvain

from .clustering import ClusteringInterface, Cluster, convert_louvain_to_clusters
from utils import visualize_community_graph
from parsing.objects import JavaFile

from ACER.src.JavaSCHA.SCHA import main as acer_main
import ACER.init_tree_sitter as init_tree_sitter


class ACERLouvainClustering(ClusteringInterface):
    def __init__(self) -> None:
        super().__init__()
        
        if not os.path.exists("ACER/build"):
            print("initializing ACER")
            init_tree_sitter.main()
        
    def cluster(self) -> list[Cluster]:
        """
        Cluster the files based on the ACER algorithm and Louvain method. 
        """
        # Run acer
        res = acer_main(input_dir="vulnerableapp", output_path="out/acer_output", fallback=True, only_variable_identifier=False, from_all=True)
        
        G = nx.Graph()
        
        for from_, tos in res.items():
            from_str = str(from_)
            for to in tos:
                G.add_edge(from_.method_name, to.method_name)
                print(type(from_), type(to))
        
        partition = community_louvain.best_partition(G.to_undirected())
    
        # Visualize the communities
        visualize_community_graph(G, partition, "out/acer_graph.png")
        
        self.clusters = convert_louvain_to_clusters(partition)
        
        return self.clusters