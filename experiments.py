import openai
import logging
import argparse
import os
import json

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

import main
from clustering.algorithms import RegexCallLouvainClustering, ACERLouvainClustering

openai_client = None

def ask_gpt(openai_client, method, model="gpt-3.5-turbo"):
    system_message = \
"""
SAST Tools are know for producing a large number of false positives. You are given the following:
1. A code snippet that was flagged as a potential vulnerability by a SAST tool.
2. The vulnerability description provided by the SAST tool.
3. 3 one-sentence summaries of the code snippet at three different levels of granularity: cluster, class, and method.

Your task is to determine if the provided code snippet is a false positive or not, given all the information you are given.
The idea is to demonstrate that with proper summaries, you can reduce the number of false positives produced by SAST tools.
However the summaries are here to support what you can see in the code snippet, so you should not rely solely on them. A combination of both should be used to make your decision.

Your ouput must have the following json format:
{
    "false_positive": true/false,
}
"""
    cluster_summary = ""
    if method.parent_cluster is not None:
        cluster_summary = method.parent_cluster.summary

    message = \
f"""
```{method.code}```
Vulnerability description: {method.vulnerability_metadata["description"]}
Cluster summary: {cluster_summary}
Class summary: {method.parent.summary}
Method summary: {method.summary}
"""

    response = openai_client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
    )
    return json.loads(response.choices[0].message.content)


def evaluate_app(app, mobsf_results, file_objects, vulnerable_methods):
    y = []
    y_true = []
    
    for vul_title, vulnerability in mobsf_results["results"].items():
        if vulnerability.get("files") is not None:
            for vulnerable_file in vulnerability["files"]:
                if vulnerable_file.get("label") is not None:
                    
                    if vulnerable_file.get("method_hash") is not None:
                        method_hash = vulnerable_file["method_hash"]
                        method = vulnerable_methods[method_hash]
                    
                        label = vulnerable_file["label"]    
                        y.append(label.get("false_positive"))
                        y_true.append(ask_gpt(openai_client, method)["false_positive"])
                        
    y = [1 if x is True else 0 if x is False else None for x in y]
    y_true = [1 if x is True else 0 if x is False else None for x in y_true]
    
    print("----- Results for", app, "-----")
    print("Number of samples: ", len(y_true))
    print(y)
    print(y_true)
    print("Accuracy: ", accuracy_score(y_true, y))
    print("Precision: ", precision_score(y_true, y))
    print("Recall: ", recall_score(y_true, y))
    print("F1: ", f1_score(y_true, y))
    print()
        

def evaluate(args):
    apps = ["damnvulnerablebank", "diva-android", "DodoVulnerableBank/DodoBank", "ovaa", "pivaa"]
    apps = ["damnvulnerablebank"]
    
    
    for app in apps:
        app_name = os.path.basename(os.path.normpath(app))
        args.mobsf_output = f"experiments/{app_name}_scan_results_processed.json"
        args.dir = os.path.join(args.dataset_dir, app)
            
        main.registered_clustering_algorithms.clear()
        main.register_clustering_algorithm(RegexCallLouvainClustering())
        main.register_clustering_algorithm(RegexCallLouvainClustering())
        main.register_clustering_algorithm(ACERLouvainClustering(), params={"input_dir": args.dir})
        
        file_objects, vulnerable_methods = main.exec_pipeline(args)
        
        with open(f"experiments/{app_name}_scan_results_processed.json") as f:
            mobsf_results = json.load(f)
        
        evaluate_app(app, mobsf_results, file_objects, vulnerable_methods)

if __name__ == "__main__":
    openai._utils._logs.logger.setLevel(logging.WARNING)
    openai._utils._logs.httpx_logger.setLevel(logging.WARNING)
    
    parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    parser.add_argument('--dataset-dir', type=str, required=False, help='Directory to scan')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    args = parser.parse_args()
    
    openai_client = openai.OpenAI(api_key=args.api_key)
    
    if args.dataset_dir is None:
        args.dataset_dir = "dataset"
    
    evaluate(args)
    # app = "DodoVulnerableBank"
    # app_name = os.path.basename(os.path.normpath(app))
    # scan_results = main.scan(os.path.join(args.dataset_dir, app))
    
    # f = open(f"experiments/{app_name}_scan_results.json", "w")
    # f.write(json.dumps(scan_results))
    # f.close()
    
