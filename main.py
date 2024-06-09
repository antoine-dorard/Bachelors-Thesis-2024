import logging
from mobsfscan.mobsfscan import MobSFScan
import json
import os
import openai
from openai import OpenAI
from datetime import datetime as dt
import argparse
from ivc.algorithms import iterative_voting_consensus
import networkx as nx

import tests

from parsing.objects import JavaFile
from parsing.parsing import extract_classes_and_methods, is_position_within_method
from clustering.algorithms import RegexCallLouvainClustering, ACERLouvainClustering
from clustering.clustering import convert_clusters_to_partition, ClusteringInterface
from clustering.consensus import create_cluster_matrix, decode_clusterings
from summarizing.summarizing import summarize_code, summarize_cluster

from utils import encode_java_files_to_json, print_clusters, visualize_community_graph
           
registered_clustering_algorithms: list[ClusteringInterface] = []

def register_clustering_algorithm(clustering_algorithm: ClusteringInterface, params: dict = None):
    if params is not None:
        clustering_algorithm.set_params(params)
    registered_clustering_algorithms.append(clustering_algorithm)

def scan(source_folder):
    scanner = MobSFScan([source_folder], json=True)
    return scanner.scan()
    

def exec_pipeline(args):
    """
    This is the pipeline function. It is responsible for executing the entire process of scanning, parsing, clustering, and summarizing the Java files.
    This method should be called be the lib user after all desired clustering algorithms are implemented, LLM's settings are set.
    
    The pipeline consists of the following steps:
        1. Scan the directory for vulnerabilities
        2. Parse the Java files
        3. Cluster the files based on the method calls
        4. Combine results of 3 if multiple clustering algorithms are used
        5. Summarize the clusters
        6. Present each vulnerability with its corresponding method and cluster summary
    """
    
    # 0) check if all clustering algorithms are registered
    if len(registered_clustering_algorithms) == 0:
        raise Exception("No clustering algorithms are registered. Please register at least one clustering algorithm before executing the pipeline.")
    
    for i, clustering_algorithm in enumerate(registered_clustering_algorithms):
        if not isinstance(clustering_algorithm, ClusteringInterface):
            raise Exception(f"Clustering algorithm at index {i} is not an instance of ClusteringInterface.")
    
    # 1)
    print(f"[{dt.now().strftime('%T.%f')[:-3]}] Scanning for vulnerabilities...")
    scan_result = scan(args.dir)
    
    with open("out/mobsf_scan.json", "w") as f:
        f.write(json.dumps(scan_result))
        
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 2a)
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Parsing Java files...")
    file_objects = []
    for file in os.listdir(args.dir): # only scans the base directory
        full_path = os.path.join(args.dir, file)
        if file.endswith(".java"):
            
            with open(full_path, "r") as f:
                java_code = f.read()
            
            current_classes = extract_classes_and_methods(java_code)
    
            jfile = JavaFile(full_path, java_code, current_classes)
            for java_class in current_classes:
                java_class.parent_file = jfile
            file_objects.append(jfile)
    
    with open("out/parsed_objects.json", "w") as f:
        f.write(encode_java_files_to_json(file_objects))
        
    # 2b) Flag vulnerable methods
    vulnerable_methods = []
    
    for file in file_objects:
        for vul_title, vulnerability in scan_result["results"].items():
            if vulnerability.get("files") is not None:
                for vulnerable_file in vulnerability["files"]:
                    
                    if file.path == vulnerable_file["file_path"]:
        
                        for java_class in file.classes:
                            for method in java_class.methods:
                                if is_position_within_method(vulnerable_file["match_position"], vulnerable_file["match_lines"], method.position):
                                    method.is_vulnerable = True
                                    method.vulnerability = vul_title
                                    method.vulnerability_metadata = vulnerability.get("metadata")
                                    method.match_string = vulnerable_file["match_string"]
                                    
                                    vulnerable_file["method"] = method # Indexing the method for later use (will be removed before saving the file)
                                    
                                    vulnerable_methods.append(method)
    
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 3)
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Clustering Java methods...")
    # cluster_fan_out = cluster(file_objects)
    # cluster_fan_out = {k: v for k, v in sorted(cluster_fan_out.items(), key=lambda item: item[1])}
    clustering_success = [False for _ in registered_clustering_algorithms]
    
    for i, clustering_algorithm in enumerate(registered_clustering_algorithms):
        try:
            clustering_algorithm.cluster(file_objects, clustering_algorithm.params)
            clustering_success[i] = True
        except Exception as e:
            clustering_success[i] = False
            print(f"/!\ Clustering algorithm at index {i} failed with exception: {e}")
            print(f"Excluding it and continuing with the next clustering algorithm...")
            
    # print("Fanout Clusters:")
    # print_clusters(fan_out.get_clusters())
    # print()
    # print("ACER Clusters:")
    # print_clusters(acer_louvain.get_clusters())
    # print()
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    # 4)
    # TODO Check for case if only one algo is registered, do not combine
    # TODO let the option to choose which algo to use for the consensus
    # Don't forget to assign parent_cluster to each method if only one clustering approach is used.
    # If consensus is used it is assigning in the decode_clusterings method.
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Combining clustering results...")
    
    all_methods = set()
    final_clusters = []
    
    if not any(clustering_success):
        raise Exception("All clustering algorithms failed. Cannot continue.")
    
    # Only one clustering algorithm succeeded -> use its results
    if clustering_success.count(True) == 1:
        print("Only one clustering algorithm succeeded. Skipping consensus.")
        true_index = clustering_success.index(True)
        all_methods = set(registered_clustering_algorithms[true_index].get_unique_methods())
        
        final_clusters = registered_clustering_algorithms[true_index].get_clusters()
        
        all_methods = list(all_methods)
    
    # More than one clustering algorithm succeeded -> combine
    else:
        print("More than one clustering algorithm succeeded. Combining results...")
        for clustering in registered_clustering_algorithms:
            if clustering_success[registered_clustering_algorithms.index(clustering)]:
                # Combine the clusters of the successful clustering algorithms here
                all_methods = clustering.get_unique_methods()
                all_methods = clustering.get_unique_methods().intersection(all_methods)
                
        all_methods = list(all_methods)
                
        cluster_matrix = create_cluster_matrix([registered_clustering_algorithms[i].get_clusters() for i in range(len(registered_clustering_algorithms)) if clustering_success[i]], all_methods)
        
        pi_star = iterative_voting_consensus(cluster_matrix, max_value=10) # Non Deterministic: might return less clusters than all approaches even if same number of clusters in each.

        final_clusters = decode_clusterings(pi_star, all_methods)
        
    # Assign corresponding parent_cluster to each method
    for method in all_methods:
        for cluster in final_clusters:
            if method in cluster.get_elements():
                method.parent_cluster = cluster

    # for cluster in decoded_clusters:
    #     print(f"Cluster with {len(cluster.get_elements())} methods.")
    #     for method in cluster.get_elements():
    #         print(method)
    
    # Visualize the consensus graph
    G = nx.Graph()
    for all_method in all_methods:
        G.add_node(all_method)
    visualize_community_graph(G, convert_clusters_to_partition(final_clusters), "out/consensus_graph.png")
    
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 5)
    
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Summarizing vulnerable methods...")
    openai_client = OpenAI(api_key=args.api_key)
    
    for vulnerable_method in vulnerable_methods: 
        print(vulnerable_method.parent.name + "." + vulnerable_method.name)
        vulnerable_method.summary = summarize_code(vulnerable_method.code, openai_client)
        
        if vulnerable_method.parent.summary == "":
            vulnerable_method.parent.summary = summarize_code(vulnerable_method.parent.code, openai_client)
        
        if vulnerable_method.parent_cluster.summary == "":
            vulnerable_method.parent_cluster.summary = summarize_cluster(vulnerable_method.parent_cluster, openai_client)
    
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 6) 
    # Add the results to the MobSF scan result 
    for vul_title, vulnerability in scan_result["results"].items():
        if vulnerability.get("files") is not None:
            for vulnerable_file in vulnerability["files"]:
                if "method" in vulnerable_file:
                    
                    vulnerable_file["summaries"] = {}
                    vulnerable_file["summaries"]["method"] = vulnerable_file["method"].summary
                    vulnerable_file["summaries"]["class"] = vulnerable_file["method"].parent.summary
                    vulnerable_file["summaries"]["cluster"] = vulnerable_file["method"].parent_cluster.summary
                    
                    del vulnerable_file["method"]
                    
    with open("out/mobsf_scan_with_summaries.json", "w") as f:
        f.write(json.dumps(scan_result))
    
    results = []
    print("===== Result =====")
    print()
    for vulnerable_method in vulnerable_methods:
        
        current_result = {
            "file": vulnerable_method.parent.parent_file.path,
            "line": vulnerable_method.position.start_line,
            "method": f"{vulnerable_method.parent.name}.{vulnerable_method.name}",
            "vulnerability": vulnerable_method.vulnerability,
            "match": vulnerable_method.match_string,
            "summaries": {
                "method": vulnerable_method.summary,
                "class": vulnerable_method.parent.summary,
                "cluster": vulnerable_method.parent_cluster.summary
            }
        }
        
        results.append(current_result)
        
        print(f"Method: {vulnerable_method.parent.name}.{vulnerable_method.name}")
        print(f"Vulnerability: {vulnerable_method.vulnerability}")
        print(f"Match: {vulnerable_method.match_string}")
        
        print("Summary")
        print(f"  Method: {vulnerable_method.summary}")
        print(f"  Class: {vulnerable_method.parent.summary}")
        print(f"  Cluster: {vulnerable_method.parent_cluster.summary}")
        print()
        
    with open("out/results.json", "w") as f:
        f.write(json.dumps({"results": results}))
    

if __name__ == '__main__':
    openai._utils._logs.logger.setLevel(logging.WARNING)
    openai._utils._logs.httpx_logger.setLevel(logging.WARNING)
    
    parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    parser.add_argument('--dir', type=str, required=True, help='Directory to scan')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    args = parser.parse_args()
    
    
    register_clustering_algorithm(RegexCallLouvainClustering())
    register_clustering_algorithm(RegexCallLouvainClustering())
    register_clustering_algorithm(ACERLouvainClustering(), params={"input_dir": args.dir})
    
    
    exec_pipeline(args)
    
    
    tests.test_all()
    