import os
import networkx as nx
import community as community_louvain
from warnings import warn
import re

from parsing.objects import JavaFile
from parsing.parsing import parse_method_calls_REGEX
from .clustering import ClusteringInterface, Cluster, convert_louvain_to_clusters
from utils import visualize_community_graph

from ACER.src.JavaSCHA.SCHA import main as acer_main
import ACER.init_tree_sitter as init_tree_sitter

class FanOutLouvainClustering(ClusteringInterface):
    def __init__(self) -> None:
        super().__init__()
        
    def cluster(self, file_objects_list: list[JavaFile], **kwargs) -> list[Cluster]:
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
                                    self.unique_methods.add(method1)
                                    self.unique_methods.add(method2)
                                    
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
    
    
class ACERLouvainClustering(ClusteringInterface):
    def __init__(self) -> None:
        super().__init__()
        
        if not os.path.exists("ACER/build"):
            print("initializing ACER")
            init_tree_sitter.main()
        
    def cluster(self, java_files, **kwargs) -> list[Cluster]:
        """
        Cluster the files based on the ACER algorithm and Louvain method. 
        """
        
        if "input_dir" not in kwargs:
            raise ValueError("input_dir is required")
        
        if "output_path" not in kwargs:
            warn("output_path is not provided. Using default path: out/acer_output")
            kwargs["output_path"] = "out/acer_output"
            
        # Run acer
        res = acer_main(input_dir=kwargs["input_dir"], output_path=kwargs["output_path"], fallback=True, only_variable_identifier=False, from_all=True)
        G = nx.Graph()
        
        for from_, tos in res.items():
            from_str = str(from_)
            for to in tos:
                obj_from = ACERLouvainClustering.get_java_method_from_signature(java_files, from_.method_name, from_.method_params, from_.contained_by)
                obj_to = ACERLouvainClustering.get_java_method_from_signature(java_files, to.method_name, to.method_params, to.contained_by)
                
                if obj_from is None or obj_to is None:
                    if obj_from is None and obj_to is None:
                        warn("Methods not found: \n" + str(from_.method_name) + " " + str(from_.method_params) + " " + str(from_.contained_by) + "\n" + str(to.method_name) + " " + str(to.method_params) + " " + str(to.contained_by))
                    elif obj_from is None:
                        warn("Method not found:"+ str(from_.method_name) + " " + str(from_.method_params) + " " + str(from_.contained_by))
                    else:
                        warn("Method not found:"+ str(to.method_name) + " " + str(to.method_params) + " " + str(to.contained_by))
                    continue
                
                self.unique_methods.add(obj_from)
                self.unique_methods.add(obj_to)
                G.add_edge(obj_from, obj_to)
        
        partition = community_louvain.best_partition(G.to_undirected())
    
        # Visualize the communities
        visualize_community_graph(G, partition, "out/acer_graph.png")
        
        self.clusters = convert_louvain_to_clusters(partition)
        
        return self.clusters
    
    @staticmethod
    def get_java_method_from_signature(files_objects: list[JavaFile], method_name: str, acer_parameters: list, acer_parent_class: str):
        """
        Get the JavaMethod object from the files_objects list based on the method's name, parameters, and parent class
        """
        acer_class_name = acer_parent_class.shorthand
        
        for jfile in files_objects:
            for jclass in jfile.classes:
                for jmethod in jclass.methods:
                    if jmethod.name == method_name and ACERLouvainClustering.compare_parameters(jmethod.parameters, acer_parameters) and jclass.name == acer_class_name:
                        return jmethod
                    else:
                        if method_name == "loadUsers":
                            ACERLouvainClustering.compare_parameters(jmethod.parameters, acer_parameters), acer_parameters
                        continue
        
        return None

    @staticmethod
    def compare_parameters(object_parameters: list, acer_parameters: list):
        """
        compare two list of parameters
        """
        if len(object_parameters) != len(acer_parameters):
            return False
        
        parameters1 = [param.type for param in object_parameters]
        acer_types = [param.strip().split(' ')[0] for param in acer_parameters]
        acer_types = [re.search(r'^[^<\[\(\?&{]*', param).group(0) for param in acer_types] # remove generics, arrays, and others from the type (TODO improve this)
        for i in range(len(parameters1)):
            if parameters1[i] != acer_types[i]:
                return False
            
        return True