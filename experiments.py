import openai
import logging
import argparse
import os
import json
from tqdm import tqdm
import csv

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

import main
from clustering.algorithms import RegexCallLouvainClustering, ACERLouvainClustering

openai_client = None

# True/False/None 

system_message = \
"""
You are a professional software developer. Specifically, you are working on designing an Android application in Java. 
After writing some code, you decide to run a Static Application Security Testing (SAST) tool to check for potential vulnerabilities in your code. 
SAST Tools are geat tools to get a quick overview of potential vulnerabilities in your code. However, they are known for producing false positives. \
A false positive is when the SAST tool flags a code snippet as a potential vulnerability, but it is not in its context. 
Your task is to determine if given all the information you are provided, the vulnerability is a false positive or not. However, it may happen that it is impossible to determine for sure \
if the vulnerability is a false positive or not, in which case you should return null. \
It is safer not to claim that a vulnerability is a false positive if you are not sure, since ignoring an actual threat could lead to serious security issues in the future. If you have only a SLIGHT suspicion that the vulnerability is a false positive, you should return false.
The information provide should only help you to make a decision when you are 100% SURE that the vulnerability is a false positive. If sensitive data may be involved in the problem, it is your role to determine whether the data is sentisitive, not or you can't tell.

Format the output as a json object with the following format:
{
    "false_positive": true/false/null
    "one_sentence_explanation": "Your explanation here"
}
"""

def gpt_setting_1(openai_client, method, model="gpt-3.5-turbo", temp=1):
    message = f"""
                -- Information provided --
                
                Vulnerability name: {method.vulnerability}
                Vulnerability description: {method.vulnerability_metadata}
                Vulnerable string in code: {method.match_string}
                """
                
    response = openai_client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        temperature=temp,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
    )
    return json.loads(response.choices[0].message.content)
    
    
    
def gpt_setting_2(openai_client, method, model="gpt-3.5-turbo", temp=1):
    
    cluster_summary = "null"
    if method.parent_cluster is not None:
        cluster_summary = method.parent_cluster.summary
        
    message = f"""
                -- Information provided --
                
                Vulnerability name: {method.vulnerability}
                Vulnerability description: {method.vulnerability_metadata}
                Vulnerable string in code: {method.match_string}
                Method code summary: {method.summary}
                Class summary: {method.parent.summary}
                Cluster summary: {cluster_summary}
                """
                
    response = openai_client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        temperature=temp,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
    )
    return json.loads(response.choices[0].message.content)

def gpt_setting_3(openai_client, method, model="gpt-3.5-turbo", temp=1):
    message = f"""
                -- Information provided --
                
                Vulnerability name: {method.vulnerability}
                Vulnerability description: {method.vulnerability_metadata}
                Vulnerable string in code: {method.match_string}
                Method code: 
                ```
                {method.code}
                ```
                """
                
    response = openai_client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        temperature=temp,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
    )
    return json.loads(response.choices[0].message.content)

def gpt_setting_4(openai_client, method, model="gpt-3.5-turbo", temp=1):
     
    
    cluster_summary = "null"
    if method.parent_cluster is not None:
        if method.parent_cluster.summary == "" or method.parent_cluster.summary is None:
            print("/!\ Cluster summary is empty")   
        cluster_summary = method.parent_cluster.summary
        
    message = f"""
                -- Information provided --
                
                Vulnerability name: {method.vulnerability}
                Vulnerability description: {method.vulnerability_metadata}
                Vulnerable string in code: {method.match_string}
                Method summary: {method.summary}
                Class summary: {method.parent.summary}
                Cluster summary: {cluster_summary}
                Method code: 
                ```
                {method.code}
                ```
                """
                
    response = openai_client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        temperature=temp,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
    )
    return json.loads(response.choices[0].message.content)

def ask_gpt(openai_client, method, setting, model="gpt-3.5-turbo", temp=1):
    if setting == 1:
        return gpt_setting_1(openai_client, method, model, temp)
    elif setting == 2:
        return gpt_setting_2(openai_client, method, model, temp)
    elif setting == 3:
        return gpt_setting_3(openai_client, method, model, temp)
    elif setting == 4:
        return gpt_setting_4(openai_client, method, model, temp)
    
    raise ValueError("setting must be between 1 and 4")


def evaluate_app(app, mobsf_results, file_objects, vulnerable_methods, setting_nb):
    y = []
    y_true = []
    
    f = open(f"experiments/results/{app}_all_results_{setting_nb}.csv", "a")
    
    for vul_title, vulnerability in tqdm(mobsf_results["results"].items()):
        if vulnerability.get("files") is not None:
            for vulnerable_file in vulnerability["files"]:
                if vulnerable_file.get("label") is not None:
                    
                    if vulnerable_file.get("method_hash") is not None:
                        method_hash = vulnerable_file["method_hash"]
                        method = vulnerable_methods[method_hash]
                    
                        label = vulnerable_file["label"] 
                        gpt_result = ask_gpt(openai_client, method, setting_nb, temp=0.7)
                        print(gpt_result["one_sentence_explanation"])
                        y.append(gpt_result["false_positive"])
                        y_true.append(label.get("false_positive"))
                        
    
    
    print("----- Results for", app, "-----")
    print("Number of samples: ", len(y_true))
    
    print(y)
    y = [1 if x is True else 0 if x is False else 0 for x in y] # if gpt's answer is None (GPT is unsure), we assume it is not a false positive because it is safer
    y_true = [1 if x is True else 0 if x is False else 0 for x in y_true]
    
    
    for i in range(len(y)):
        if i < len(y) - 1:
            f.write(str(y[i]) + ",")
        else:
            f.write(str(y[i]))
            
    f.write("\n")
    f.close()
    
    print(y)
    print(y_true)
    print("Accuracy: ", accuracy_score(y_true, y))
    print("Precision: ", precision_score(y_true, y, zero_division=0))
    print("Recall: ", recall_score(y_true, y, zero_division=0))
    print("F1: ", f1_score(y_true, y, zero_division=0))
    print()
        

def evaluate(args):
    apps = ["damnvulnerablebank", "diva-android", "DodoVulnerableBank/DodoBank", "ovaa", "pivaa"]
    apps = ["damnvulnerablebank"]
    
    setting = 4
    
    for app in apps:
        app_name = os.path.basename(os.path.normpath(app))
        args.mobsf_output = f"experiments/json/{app_name}_scan_results_processed.json"
        args.dir = os.path.join(args.dataset_dir, app)
            
        main.registered_clustering_algorithms.clear()
        main.register_clustering_algorithm(RegexCallLouvainClustering())
        main.register_clustering_algorithm(RegexCallLouvainClustering())
        main.register_clustering_algorithm(ACERLouvainClustering(), params={"input_dir": args.dir})
        
        file_objects, vulnerable_methods = main.exec_pipeline(args)
        
        with open(f"experiments/json/{app_name}_scan_results_processed.json") as f:
            mobsf_results = json.load(f)
            
        print("Evaluating", app, "...")
        evaluate_app(app, mobsf_results, file_objects, vulnerable_methods, setting)

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
        
    args.__setattr__("summarize", False)
    if not os.path.exists("experiments/results"):
        os.makedirs("experiments/results")
        
    evaluate(args)
    
    import metrics
    metrics.aggregate_metrics("damnvulnerablebank")
    # app = "DodoVulnerableBank"
    # app_name = os.path.basename(os.path.normpath(app))
    # scan_results = main.scan(os.path.join(args.dataset_dir, app))
    
    # f = open(f"experiments/json/{app_name}_scan_results.json", "w")
    # f.write(json.dumps(scan_results))
    # f.close()
    
