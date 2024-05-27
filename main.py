import logging
from mobsfscan.mobsfscan import MobSFScan
import json
import os
import openai
from openai import OpenAI
from datetime import datetime as dt
import argparse
import javalang
import re
import networkx as nx
import matplotlib.pyplot as plt
import community as community_louvain

import tests
from objects import JavaFile, JavaClass, JavaMethod, Position
from utils import get_method_signature_tostr, encode_java_files_to_json

def cluster(file_objects_list):
    # Cluster the files based on the method calls
    
    G = nx.Graph()
    
    for file1 in file_objects_list:
        for java_class1 in file1.classes:
            for method1 in java_class1.methods:
                
                parsed_calls = parse_method_calls_REGEX(method1.code)
                
                for file2 in file_objects_list:
                    for java_class2 in file2.classes:
                        for method2 in java_class2.methods:
                            if method1 == method2:
                                continue
                            
                            if not G.has_edge(method1, method2):
                                G.add_edge(method1, method2)
                                G[method1][method2]["calls"] = 0
                            
                            if method2.name in parsed_calls:
                                count = parsed_calls.count(method2.name)
                                G[method1][method2]["calls"] += count
                                
                                
    # print edges and their value
    # for edge in G.edges():
    #     print(f"{edge[0].parent.name}.{edge[0].name} - {edge[1].parent.name}.{edge[1].name}: {G[edge[0]][edge[1]]['calls']}")
    
    for edge in G.edges():
        if G[edge[0]][edge[1]]['calls'] <= 0:
            G.remove_edge(edge[0], edge[1])
            
    partition = community_louvain.best_partition(G.to_undirected())

    # Visualize the communities
    # pos = nx.spring_layout(G)
    # cmap = plt.get_cmap('viridis', max(partition.values()) + 1)
    # nx.draw_networkx_nodes(G, pos, partition.keys(), node_size=2000, cmap=cmap, node_color=list(partition.values()))
    # nx.draw_networkx_edges(G, pos, alpha=0.5)
    # nx.draw_networkx_labels(G, pos)
    # plt.savefig("graph.png")
        
    return partition
                            
                            

def scan(source_folder):
    scanner = MobSFScan([source_folder], json=True)
    return scanner.scan()

def parse_method_calls_REGEX(method_body) -> list[str]:
    code = method_body.split(";")
   
   # The following regex returns all unqualified calls (i.e. calls without the class or instance  name) in the code. Will match contructor calls as well.
    method_call_pattern = re.compile(r'(?!\bif\b|\bfor\b|\bwhile\b|\bswitch\b|\btry\b|\bcatch\b|\bsealed\b|\bnon-sealed\b)(\b[\w]+\b)[\s\n\r]*(?=\(.*\))')

    method_calls = []
    for line in code:
        matches = method_call_pattern.findall(line)
        method_calls.extend(matches)
        
    return method_calls

def parse_method_calls_LLM(method_body, openai_client, model="gpt-3.5-turbo"):
    system_message = """
You are a Senior Java Developer and understand the language like no one.  You are given a series of Java lines of code altogether constituting a Java method.

Your role is to reply with any method call that you detect within those lines. 
Format your replies as follows and do never write something else than this. You may however write more than one method call if you read more than one on one line. 
(ClassName) instanceName.methodName

Note: there might be no method calls on a line, in which case you reply None. (Constructor calls or not considered method calls)

Example:
Input: if(hex.length() == 1) hexString.append('0');
Output: 
hex.length
hexString.append
    """
    
    code = method_body.splitlines()
    calls = []
    messages = [
        {"role": "system", "content": system_message}
    ]
    
    
    for line in code:
        messages.append({"role": "user", "content": line})
        
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages
        )
        
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        
        if response.choices[0].message.content != "None":
            calls.append(response.choices[0].message.content)

    return calls


def summarize(code, openai_client, model="gpt-3.5-turbo"):
    system_message = """
You are a professional Java code interpreter. Your role is to summarize code while strictly following the two following main rules:
1. PRECISENESS: Always be as precise as possible. You must include everything relevant.
2. CONCISENESS: always keep the summary concise, while not breaking the first rule.

You may be given to interpret entire Java files, classes, or only methods.
If you are given a file, create a few points summary of what that file does, without explaining the details for each method.
The summary should be a high-level overview of the file's purpose and functionality and not a line-by-line or method by method explanation.
    """
    
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": code}
        ]
    )
    return response.choices[0].message.content
    

def is_position_within_method(mobsf_position, mobsf_lines, method):
    if mobsf_lines[0] == mobsf_lines[1]: # if the detected vulnerability is on one line
        if method.start_line < mobsf_lines[0] and method.end_line > mobsf_lines[0]: # if the vulnerability is strictly within the method
            return True
        elif method.start_line == mobsf_lines[0] or method.end_line == mobsf_lines[0]: # if the vulnerability is on the first or last line of the method
            if method.start_col <= mobsf_position[0] and method.end_col >= mobsf_position[1]: # if the vulnerability is strictly within the method
                return True
    else:
        if method.start_line <= mobsf_lines[0] and method.end_line >= mobsf_lines[1]:
            return True
        elif method.start_line == mobsf_lines[0] or method.end_line == mobsf_lines[1]:
            if method.start_line == mobsf_lines[0] and method.start_col <= mobsf_position[0]:
                return True
    return False
    # TODO Check if the position is within the method. Use this function to summarize only methods that contain vulnerabilities - Make tests


def extract_and_summarize(java_code: str, openai_client: str, include_summary=True):
    tree = javalang.parse.parse(java_code)
    class_stack = []
    
    classes = []
    
    java_code = java_code.splitlines()

    # Traverse the AST and keep track of class contexts
    for path, node in tree:
        if isinstance(node, javalang.tree.ClassDeclaration):
            class_stack.append(node.name)            
            
            code, end_line, end_col = extract_java_methods_body(java_code, node.position.line, node.position.column)
            code = "\n".join(code)
            pos = Position(node.position.line, end_line, node.position.column, end_col)
            
            summary = ""
            if include_summary:
                summary = summarize(code, openai_client)
                
            classes.append(JavaClass(node.name, pos, code, summary))
            
        elif isinstance(node, javalang.tree.MethodDeclaration):
            current_class = class_stack[-1] if class_stack else None
            
            code, end_line, end_col = extract_java_methods_body(java_code, node.position.line, node.position.column)
            code = "\n".join(code)
            position = {
                "start_line": node.position.line,
                "end_line": end_line,
                "start_col": node.position.column,
                "end_col": end_col
            }
            
            summary = ""
            if include_summary:
                summary = summarize(code, openai_client)
                    
            current_return_type = "void"
            if node.return_type:
                current_return_type = node.return_type.name
                
            if current_class == classes[-1].name:
                classes[-1].add_new_method(
                    node.name, 
                    current_return_type, 
                    [{"name": param.name, "type": param.type.name} for param in node.parameters],
                    Position(node.position.line, end_line, node.position.column, end_col),
                    code, 
                    summary
                )
                
            else:
                for c in classes:
                    if c.name == current_class:
                        c.add_new_method(
                            node.name, 
                            current_return_type, 
                            [{"name": param.name, "type": param.type.name} for param in node.parameters],
                            Position(node.position.line, end_line, node.position.column, end_col), 
                            code, 
                            summary
                        )
                        break    
    return classes
            
            
def extract_java_methods_body(lines, start_line, start_col):
    """
    Extracts the body of a Java method from the source code lines.

    This function finds and extracts the complete body of a Java method starting from the specified line and column.
    It correctly handles nested curly braces to ensure only the code within the method is included. The extraction
    process stops once the braces are balanced, indicating the end of the method body.

    Args:
    lines (list of str): The lines of source code.
    start_line (int): The line number where the method signature starts.
    start_col (int): The column number where the method signature starts, which is be right before the method's
                     return type.

    Returns:
    tuple containing list of str: Contains the lines of code that make up the method's body, including the signature and continuing 
                 until the closing brace is found.
    and int: The line number where the method body ends.
    """
    
    # TODO Check for semi colon before first opening brackets to skip if interface or abstract method declaration 
    
    current_line_index = start_line - 1  # Adjust index to be zero-based for list access
    signature = lines[current_line_index][start_col - 1:]  # Extract the method signature starting from the given column
    lines[current_line_index] = lines[current_line_index][start_col - 1:]  # Modify the line to start from the method signature
    
    # Check if there are braces on the current signature line
    brace_total_count = signature.count('{') + signature.count('}')
    
    # Advance to the line containing the opening brace
    while brace_total_count == 0:
        if current_line_index + 1 < len(lines):
            current_line_index += 1
        else:
            break
        brace_total_count = lines[current_line_index].count('{') + lines[current_line_index].count('}')
    
    # If no braces are found after the signature line, exit the function
    if current_line_index + 1 == len(lines) and brace_total_count == 0:
        raise Exception("No brackets found")
    
    # Find the position of the first opening brace after the method signature
    current_char = 0
    while lines[current_line_index][current_char] != '{' and current_char < len(lines[current_line_index]):
        current_char += 1
    
    # Include the entire start line if the opening brace is not on the same line as the method signature
    if current_line_index != start_line - 1:
        method_code = [signature]
    else:
        method_code = []
    
    brace_count = 1  # Initialize brace count since an opening brace was found
    current_char += 1  # Move past the opening brace
    
    # Process the remaining characters in the lines
    while current_line_index < len(lines):
        while current_char < len(lines[current_line_index]):
            if lines[current_line_index][current_char] == '{':
                brace_count += 1
            elif lines[current_line_index][current_char] == '}':
                brace_count -= 1
            
            if brace_count == 0:  # If braces balance out, append and return the method body up to this point
                method_code.append(lines[current_line_index][:current_char + 1])
                return (method_code, current_line_index + 1, current_char + 1)
        
            current_char += 1
            
        method_code.append(lines[current_line_index])  # Add the whole line to the method body
        current_line_index += 1
        current_char = 0  # Reset character index for the new line
    
    raise Exception("No closing brace found")
    
def run(overriding_dir=None, scan=True):
    # get api key of LLM model (currently @ openai) and directory to scan
    parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    parser.add_argument('--dir', type=str, required=True, help='Directory to scan')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    args = parser.parse_args()
    
    openai_client = OpenAI(api_key=args.api_key)
    
    directory = ""
    if overriding_dir:
        directory = overriding_dir
    else:
        directory = args.dir
    
    if scan:
        print(f"[{dt.now().strftime('%H:%M:%S')}] Scanning for vulnerabilities...")
        scan_result = scan(args.dir)
        print(f"[{dt.now().strftime('%H:%M:%S')}] Done.")
    
    file_objects = []
    for file in os.listdir(directory): # only scans the base directory
        full_path = os.path.join(directory, file)
        if file.endswith(".java"):
            print()
            print(f"[{dt.now().strftime('%H:%M:%S')}] Processing file {full_path}...")
            
            with open(full_path, "r") as f:
                java_code = f.read()
            
            current_classes = extract_and_summarize(java_code, openai_client, include_summary=False)
    
            file_objects.append(JavaFile(full_path, java_code, current_classes))
    
    if scan:
        with open("output_scan.json", "w") as f:
            f.write(json.dumps(scan_result))
        
    with open("output_objects.json", "w") as f:
        f.write(encode_java_files_to_json(file_objects))

    cluster_fan_out = cluster(file_objects)
    

if __name__ == '__main__':
    openai._utils._logs.logger.setLevel(logging.WARNING)
    openai._utils._logs.httpx_logger.setLevel(logging.WARNING)
    
    run(overriding_dir="vulnerableapp", scan=False)
    
    tests.test_all()
    