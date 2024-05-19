from mobsfscan.mobsfscan import MobSFScan
import json
import os
from openai import OpenAI
from datetime import datetime as dt
import argparse
import javalang
import tests

def cluster(source_folder):
    pass

def scan(source_folder):
    scanner = MobSFScan([source_folder], json=True)
    return scanner.scan()

def summarize(source_folder):

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "user", "content": "Where was it played?"}
        ]
    )
    
def get_method_signature_tostr(node):
    signature = ""
    if node.return_type:
        signature += node.return_type.name + " "
    else:
        signature += "void "
        
    signature += node.name + "("
    
    for i, param in enumerate(node.parameters):
        signature += param.type.name + " " + param.name
        if i < len(node.parameters) - 1:
            signature += ", "
            
    signature += ")"
    
    return signature

# Works only when the file is is formatted correctly (i.e. no syntax errors, and line by line code) 
def extract_java_methods(java_code):
    tree = javalang.parse.parse(java_code)
    methods = []
    class_stack = []
    
    # obj = {}
    # obj["classes"] = {}

    # Traverse the AST and keep track of class contexts
    for path, node in tree:
        if isinstance(node, javalang.tree.ClassDeclaration):
            class_stack.append(node.name)
            print()
            print(f"Class: {node.name}")
        elif isinstance(node, javalang.tree.MethodDeclaration):
            current_class = class_stack[-1] if class_stack else None
            print(get_method_signature_tostr(node))
            methods.append((current_class, node.position.line, node))

    method_bodies = []
    lines = java_code.splitlines()

    for current_class, start_line, method in methods:
        
        method_code = extract_java_methods_body(lines, start_line, method.position.column)
        
        method_bodies.append((current_class, method.name, "\n".join(method_code)))

    return method_bodies
    
    
class Summary:
    system = """
        You are a professional Java code interpreter. Your role is to summarize code while strictly following the two following main rules:
        1. PRECISENESS: Always be as precise as possible. You must include everything relevant.
        2. CONCISENESS: always keep the summary concise, while not breaking the first rule.

        You may be given to interpret entire Java files, classes, or only methods.
        If you are given a file, create a few points summary of what that file does, without explaining the details for each method.
        The summary should be a high-level overview of the file's purpose and functionality and not a line-by-line or method by method explanation.
    """
    
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        
    def summarize(self, code, model="gpt-3.5-turbo"):
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": self.system},
                {"role": "user", "content": code}
            ]
        )
        return response.choices[0].message.content
    
    def summarize_file(self, file, model="gpt-3.5-turbo"):
        with open(file, "r") as f:
            code = f.read()
        return self.summarize(code, model)
    
    def summarize_classes_and_methods(self, file, model="gpt-3.5-turbo"):
        with open(file, 'r') as f:
            java_code = f.read()
            
        methods = extract_java_methods(java_code)
        
        file_summary = {}
    
        return methods
            
            
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
    list of str: Contains the lines of code that make up the method's body, including the signature and continuing 
                 until the closing brace is found.
    """
    
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
            
            current_char += 1
            if brace_count == 0:  # If braces balance out, append and return the method body up to this point
                method_code.append(lines[current_line_index][:current_char + 1])
                return method_code
        
        method_code.append(lines[current_line_index])  # Add the whole line to the method body
        current_line_index += 1
        current_char = 0  # Reset character index for the new line
    
    raise Exception("No closing brace found")
    
def run():
    # get api key of LLM model (currently @ openai)
    parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    args = parser.parse_args()
    
    
    print(f"[{dt.now().strftime('%H:%M:%S')}] Scanning for vulnerabilities...")
    scan_result = scan("vulnerableapp")
    # scan = scan("Report.java")
    
    f_output_summary = open("output_summary.json", "a")
    summary = Summary(api_key=args.api_key)
    for file in os.listdir("vulnerableapp"): # only scans the base directory
        print(f"[{dt.now().strftime('%H:%M:%S')}] Summarizing file {file}...")
        if file.endswith(".java"):
            summary_content = summary.summarize_file(os.path.join("vulnerableapp", file))
            print(summary_content)
            print("\n\n")
            
            f_output_summary.write("File: " + file + "\n")
            f_output_summary.write(summary_content + "\n")
            f_output_summary.write("\n\n")
    
    with open("output_scan.json", "w") as f:
        f.write(json.dumps(scan_result))


if __name__ == '__main__':
    # run()
    
    parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    args = parser.parse_args()
    
    summary = Summary(api_key=args.api_key)
    # summary.summarize_classes_and_methods("vulnerableapp/DBManager.java")
          
    tests.test_extract_java_methods()
    
    