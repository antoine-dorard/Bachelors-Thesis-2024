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
from parsing.parsing import extract_classes_and_methods
from clustering.algorithms import FanOutLouvainClustering, ACERLouvainClustering
from clustering.clustering import convert_clusters_to_partition
from clustering.majority import create_cluster_matrix, decode_clusterings

from utils import encode_java_files_to_json, print_clusters, visualize_community_graph
           

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
    
    # 1)
    print(f"[{dt.now().strftime('%T.%f')[:-3]}] Scanning for vulnerabilities...")
    scan_result = scan(args.dir)
    
    with open("output_scan.json", "w") as f:
        f.write(json.dumps(scan_result))
        
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 2)
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Parsing Java files..")
    file_objects = []
    for file in os.listdir(args.dir): # only scans the base directory
        full_path = os.path.join(args.dir, file)
        if file.endswith(".java"):
            
            with open(full_path, "r") as f:
                java_code = f.read()
            
            current_classes = extract_classes_and_methods(java_code)
    
            file_objects.append(JavaFile(full_path, java_code, current_classes))
    
    with open("output_objects.json", "w") as f:
        f.write(encode_java_files_to_json(file_objects))
        
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 3)
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Clustering Java files..")
    # cluster_fan_out = cluster(file_objects)
    # cluster_fan_out = {k: v for k, v in sorted(cluster_fan_out.items(), key=lambda item: item[1])}
    fan_out = FanOutLouvainClustering()
    fan_out.cluster(file_objects)
    
    acer_louvain = ACERLouvainClustering()
    acer_louvain.cluster(file_objects, input_dir=args.dir)
    
    print("Fanout Clusters:")
    print_clusters(fan_out.get_clusters())
    print()
    print("ACER Clusters:")
    print_clusters(acer_louvain.get_clusters())
    print()
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    # 4)
    # TODO Check for case if only one algo is registered, do not combine
    # TODO let the option to choose which algo to use for the consensus

    all_methods = list(fan_out.get_unique_methods().intersection(acer_louvain.get_unique_methods()))        
    
    cluster_matrix = create_cluster_matrix((fan_out.get_clusters(), acer_louvain.get_clusters()), all_methods)
    
    pi_star = iterative_voting_consensus(cluster_matrix, max_value=10) # Non Deterministic: might return less clusters than all approaches even if same number of clusters in each.

    decoded_clusters = decode_clusterings(pi_star, all_methods)

    for cluster in decoded_clusters:
        print(f"Cluster with {len(cluster.get_elements())} methods.")
        for method in cluster.get_elements():
            print(method)
    
    # Visualize the consensus graph
    G = nx.Graph()
    for all_method in all_methods:
        G.add_node(all_method)
    visualize_community_graph(G, convert_clusters_to_partition(decoded_clusters), "out/consensus_graph.png")
    
    # 5)
    openai_client = OpenAI(api_key=args.api_key)
    
    
    

if __name__ == '__main__':
    openai._utils._logs.logger.setLevel(logging.WARNING)
    openai._utils._logs.httpx_logger.setLevel(logging.WARNING)
    
    parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    parser.add_argument('--dir', type=str, required=True, help='Directory to scan')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    args = parser.parse_args()
    
    exec_pipeline(args)
    
    
    tests.test_all()
    