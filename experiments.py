import openai
import logging
import argparse
import os
import json

import main
from clustering.algorithms import RegexCallLouvainClustering, ACERLouvainClustering

def evaluate(args):
    # 1) first scan all apps with mobsf, get the json scan results and flag the false positivies manually (check in the respective repo if they include a list of the false positives)
    # Actually check what are the know vulnerabilities and check the additional ones that are not in the list and that MobSF flags?
    openai_client = openai.Openai(api_key=args.api_key)
    
    MobSF_results = {}
    
    for app_dir in os.listdir(args.dataset_dir):
        args = {"dir": args.dataset_dir + app_dir, "api_key": args.api_key}
        file_objects, vulnerable_methods = main.exec_pipeline(args)
        
    # 2) Compute metrics
    y = []
    y_true = []
    
    for method in vulnerable_methods:
        y.append(method.is_false_positive)
        y_true.append(ask_gpt(openai_client, method))
        
    
        
        


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

    message = \
f"""
```{method.code}```
Vulnerability description: {method.vulnerability_description}
Cluster summary: {method.cluster_summary}
Class summary: {method.class_summary}
Method summary: {method.method_summary}
"""

    response = openai_client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    openai._utils._logs.logger.setLevel(logging.WARNING)
    openai._utils._logs.httpx_logger.setLevel(logging.WARNING)
    
    parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    parser.add_argument('--dataset-dir', type=str, required=True, help='Directory to scan')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    args = parser.parse_args()
    
    
    # evaluate(args)
    app = "DodoVulnerableBank"
    scan_results = main.scan(os.path.join(args.dataset_dir, app))
    
    f = open(f"experiments/{app}_scan_results.json", "w")
    f.write(json.dumps(scan_results))
    f.close()
    
