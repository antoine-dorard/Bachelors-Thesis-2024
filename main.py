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
import traceback
from tqdm import tqdm

import tests

from parsing.objects import JavaFile
from parsing.parsing import extract_classes_and_methods, is_position_within_method
from clustering.algorithms import RegexCallLouvainClustering, ACERLouvainClustering
from clustering.clustering import convert_clusters_to_partition, ClusteringInterface
from clustering.consensus import create_cluster_matrix, decode_clusterings
from summarizing.summarizing import summarize_code, summarize_cluster

from utils import encode_java_files_to_json, print_clusters, visualize_community_graph
           
registered_clustering_algorithms: list[ClusteringInterface] = []

def register_clustering_algorithm(clustering_algorithm: ClusteringInterface, params: dict = None) -> None:
    """
    Register a clustering algorithm to be used in the pipeline.
    """
    if params is not None:
        clustering_algorithm.set_params(params)
    registered_clustering_algorithms.append(clustering_algorithm)

def scan(source_folder: str) -> dict:
    """
    Scan the application directory for vulnerabilities using MobSF.
    """
    scanner = MobSFScan([source_folder], json=True)
    return scanner.scan()
    

def exec_pipeline(args):
    """
    This is the pipeline function. It is responsible for executing the entire process of scanning, parsing, clustering, and summarizing the Java files.
    This method should be called by the user after all desired clustering algorithms are implemented and registered wih the function register_clustering_algorithm.
    
    The pipeline consists of the following steps:
        1. Scan the directory for vulnerabilities using MobSF
        2. Parse the Java files
        3. Cluster the files based on the method calls
        4. Combine results of 3 if multiple clustering algorithms are used
        5. Summarize the clusters
        6. Present each vulnerability with its corresponding method and cluster summary
        
    Parameters:
    args (argparse.Namespace): The arguments passed to the pipeline from the terminal: --dir, --api-key, --mobsf-output, --summarize, --debug
    """
    
    # 0) check if all clustering algorithms are registered
    if len(registered_clustering_algorithms) == 0:
        raise Exception("No clustering algorithms are registered. Please register at least one clustering algorithm before executing the pipeline.")
    
    for i, clustering_algorithm in enumerate(registered_clustering_algorithms):
        if not isinstance(clustering_algorithm, ClusteringInterface):
            raise Exception(f"Clustering algorithm at index {i} is not an instance of ClusteringInterface.")
    
    # 1) Load report or mobsf scan app
    scan_result = None
    if args.mobsf_output is not None:
        with open(args.mobsf_output, "r") as f:
            scan_result = json.load(f)
            
    else:
        print(f"[{dt.now().strftime('%T.%f')[:-3]}] Scanning for vulnerabilities...")
        scan_result = scan(args.dir)
        
        with open("out/mobsf_scan.json", "w") as f:
            f.write(json.dumps(scan_result))
            
        print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 2a)
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Parsing Java files...")
    file_objects = []
    for dirpath, dirnames, filenames in os.walk(args.dir):
        for file in filenames:
            if file.endswith(".java"):
                full_path = os.path.join(dirpath, file)
                with open(full_path, "r") as f:
                    java_code = f.read()

                current_classes = extract_classes_and_methods(java_code)
                jfile = JavaFile(full_path, java_code, current_classes)
                
                for java_class in current_classes:
                    java_class.parent_file = jfile
                
                file_objects.append(jfile)
        
    # 2b) Flag vulnerable methods
    vulnerable_methods = {}
    
    for file in file_objects:
        for vul_title, vulnerability in scan_result["results"].items():
            if vulnerability.get("files") is not None:
                for vulnerable_file in vulnerability["files"]:
                    
                    if file.path == vulnerable_file["file_path"]:
        
                        for java_class in file.classes:
                            for method in java_class.methods:
                                
                                if is_position_within_method(vulnerable_file["match_position"], vulnerable_file["match_lines"], method.position):
                                    label = vulnerable_file.get("label")
                                    if label is not None:
                                        method.is_false_positive = label.get("false_positive") 
                                    method.is_vulnerable = True
                                    method.vulnerability = vul_title
                                    method.vulnerability_metadata = vulnerability.get("metadata")
                                    method.match_string = vulnerable_file["match_string"]
                                    
                                    vulnerable_methods[method.__hash__()] = method   
                                    
                                    if args.summarize is not True and vulnerable_file.get("summaries") is not None:
                                        summaries = vulnerable_file["summaries"]
                                        method.summary = summaries["method"]
                                        method.parent.summary = summaries["class"]
                                
                                        method.cluster_summary = summaries["cluster"] # Don't have attribute parent_cluster yet, so we store it here for now.
                                        
                                    vulnerable_file["method"] = method # Indexing the method for later use (will be removed before saving the file)
    
    
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 3)
    
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Clustering Java methods...")
    
    clustering_success = [False for _ in registered_clustering_algorithms]
    
    for i, clustering_algorithm in enumerate(registered_clustering_algorithms):
        try:
            clustering_algorithm.cluster(file_objects, clustering_algorithm.params)
            clustering_success[i] = True
        except Exception as e:
            clustering_success[i] = False
            print(f"/!\ Clustering algorithm at index {i} failed with exception:")
            if args.debug:
                print(traceback.format_exc())
            else:
                print(e)
            print(f"Excluding it and continuing with the next clustering algorithm...")
            

    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 4)
    
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Combining clustering results...")
    
    all_methods = set()
    final_clusters = []
    
    if not any(clustering_success):
        raise Exception("All clustering algorithms failed. Cannot continue.")
    
    # Only one clustering algorithm succeeded -> use its results
    if clustering_success.count(True) == 1:
        print("Only one clustering algorithm succeeded. Skipping consensus.")
        true_index = clustering_success.index(True)
        all_methods = list(registered_clustering_algorithms[true_index].get_unique_methods())
        
        final_clusters = registered_clustering_algorithms[true_index].get_clusters()
    
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
    
    # Visualize the consensus graph
    G = nx.Graph()
    for all_method in all_methods:
        G.add_node(all_method)
    visualize_community_graph(G, convert_clusters_to_partition(final_clusters), "out/consensus_graph.png")
    
    print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 5)
    
    if args.summarize is True:
        print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Summarizing vulnerable methods...")
        openai_client = OpenAI(api_key=args.api_key)
        
        for vulnerable_method in tqdm(vulnerable_methods.values()): 
            vulnerable_method.summary = summarize_code(vulnerable_method.code, openai_client)
            
            if vulnerable_method.parent.summary == "":
                vulnerable_method.parent.summary = summarize_code(vulnerable_method.parent.code, openai_client)
            
            if vulnerable_method.parent_cluster is not None and vulnerable_method.parent_cluster.summary == "":
                vulnerable_method.parent_cluster.summary = summarize_cluster(vulnerable_method.parent_cluster, openai_client)
            elif vulnerable_method.parent_cluster is None:
                print("Parent cluster is None, skipping summarization of parent cluster for this method.")
        
        print(f"[{dt.now().strftime('%H:%M:%S.%f')[:-3]}] Done.")
    
    # 6) 
    # Add the results to the MobSF scan result 
    for vul_title, vulnerability in scan_result["results"].items():
        if vulnerability.get("files") is not None:
            for vulnerable_file in vulnerability["files"]:
                if "method" in vulnerable_file:
                    
                    if args.summarize is True:
                        cluster_summary = "Cluster could not be determined for this method."
                        if vulnerable_file["method"].parent_cluster is not None:
                            cluster_summary = vulnerable_file["method"].parent_cluster.summary # Assign the cluster summary to the parent cluster object

                        vulnerable_file["summaries"] = {}
                        vulnerable_file["summaries"]["method"] = vulnerable_file["method"].summary
                        vulnerable_file["summaries"]["class"] = vulnerable_file["method"].parent.summary
                        vulnerable_file["summaries"]["cluster"] = cluster_summary
                    else:
                        if vulnerable_file["method"].parent_cluster is not None:
                            vulnerable_file["method"].parent_cluster.summary = vulnerable_file["summaries"]["cluster"]
                    
                    vulnerable_file["method_hash"] = vulnerable_file["method"].__hash__() # Used in experiments to lookup for the method object from the scan_results json file
                    
                    del vulnerable_file["method"]
                    
    with open("out/mobsf_scan_with_summaries.json", "w") as f:
        f.write(json.dumps(scan_result))
        
    app_name = os.path.basename(os.path.normpath(args.dir))
    with open(f"experiments/json/{app_name}_scan_results_processed.json", "w") as f:
        f.write(json.dumps(scan_result))
    
    results = []
    print("===== Result =====")
    print()
    for vulnerable_method in vulnerable_methods.values():
        
        cluster_summary = "Cluster could not be determined for this method."
        if vulnerable_method.parent_cluster is not None:
            cluster_summary = vulnerable_method.parent_cluster.summary
        
        current_result = {
            "file": vulnerable_method.parent.parent_file.path,
            "line": vulnerable_method.position.start_line,
            "method": f"{vulnerable_method.parent.name}.{vulnerable_method.name}",
            "vulnerability": vulnerable_method.vulnerability,
            "match": vulnerable_method.match_string,
            "summaries": {
                "method": vulnerable_method.summary,
                "class": vulnerable_method.parent.summary,
                "cluster": cluster_summary
            }
        }
        
        results.append(current_result)
        
        print(f"Method: {vulnerable_method.parent.name}.{vulnerable_method.name}")
        print(f"Vulnerability: {vulnerable_method.vulnerability}")
        print(f"Match: {vulnerable_method.match_string}")
        
        print("Summary")
        print(f"  Method: {vulnerable_method.summary}")
        print(f"  Class: {vulnerable_method.parent.summary}")
        print(f"  Cluster: {cluster_summary}")
        print()
        
    with open("out/results.json", "w") as f:
        f.write(json.dumps({"results": results}))
        
    return file_objects, vulnerable_methods
    

if __name__ == '__main__':
    """
    Pipeline entry point if run from the terminal.
    
    Terminal arguments:
    --dir (Required): Directory to scan
    --api-key (Required): OpenAI API key
    --mobsf-output (Optional): Path to the MobSF scan output file if it has already been run.
    --summarize (Optional): Whether to summarize the methods or not. Default is True.
    --debug (Optional): Whether to print full stack traces or not during runtime. Default is False.
    """
    openai._utils._logs.logger.setLevel(logging.WARNING)
    openai._utils._logs.httpx_logger.setLevel(logging.WARNING)
    
    parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    parser.add_argument('--dir', type=str, required=True, help='Directory to scan')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    parser.add_argument('--mobsf-output', type=str, required=False, help='OpenAI API key')
    parser.add_argument('--summarize', type=str, required=False, help='OpenAI API key', default=True)
    parser.add_argument('--debug', type=str, required=False, help='OpenAI API key', default=False)
    
    args = parser.parse_args()
    
    # Register clustering algorithms here before executing the pipeline
    register_clustering_algorithm(RegexCallLouvainClustering())
    register_clustering_algorithm(RegexCallLouvainClustering())
    register_clustering_algorithm(ACERLouvainClustering(), params={"input_dir": args.dir})
    
    # Execute the pipeline
    exec_pipeline(args)
    
    # Some tests are performed on the parser
    tests.test_all()
    