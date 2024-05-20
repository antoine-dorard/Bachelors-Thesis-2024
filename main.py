import logging
from mobsfscan.mobsfscan import MobSFScan
import json
import os
import openai
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
            
        print("User", line)
        print("Assistant", response.choices[0].message.content)

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

def isPositionWithinMethod(mobsf_position, mobsf_lines, method):
    # TODO Check if the position is within the method. Use this function to summarize only methods that contain vulnerabilities
    pass


def extract_and_summarize(java_code: str, openai_client: str, include_summary=True):
    tree = javalang.parse.parse(java_code)
    methods = []
    class_stack = []
    
    obj = {}
    obj["classes"] = []
    
    java_code = java_code.splitlines()

    # Traverse the AST and keep track of class contexts
    for path, node in tree:
        if isinstance(node, javalang.tree.ClassDeclaration):
            class_stack.append(node.name)
            print()
            print(f"Class: {node.name}")
            
            
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
                
            obj["classes"].append({"name": node.name, 
                                   "position": position, 
                                   "code": code,
                                   "summary": summary,
                                   "methods": []
                                   })
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
                
            if current_class == obj["classes"][-1]["name"]:
                print(get_method_signature_tostr(node))
                obj["classes"][-1]["methods"].append({"name": node.name, 
                                                      "signature": get_method_signature_tostr(node),
                                                      "position": position, 
                                                      "code": code,
                                                      "summary": summary
                                                      })
            else:
                for c in obj["classes"]:
                    if c["name"] == current_class:
                        c["methods"].append({"name": node.name, 
                                             "signature": get_method_signature_tostr(node),
                                             "position": position, 
                                             "code": code,
                                             "summary": summary
                                             })
                        break
                    
    #         print(get_method_signature_tostr(node))
    #         methods.append((current_class, node.position.line, node))

    # method_bodies = []
    # lines = java_code.splitlines()

    # for current_class, start_line, method in methods:
        
    #     method_code = extract_java_methods_body(lines, start_line, method.position.column)
        
    #     method_bodies.append((current_class, method.name, "\n".join(method_code)))

    # return method_bodies
    return obj
            
            
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
    
def run(overriding_dir=None):
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
    
    print(f"[{dt.now().strftime('%H:%M:%S')}] Scanning for vulnerabilities...")
    scan_result = scan(args.dir)
    print(f"[{dt.now().strftime('%H:%M:%S')}] Done.")
    
    obj = []
    for file in os.listdir(directory): # only scans the base directory
        full_path = os.path.join(directory, file)
        if file.endswith(".java"):
            print()
            print(f"[{dt.now().strftime('%H:%M:%S')}] Processing file {full_path}...")
            
            with open(full_path, "r") as f:
                java_code = f.read()
            
            current_obj = extract_and_summarize(java_code, openai_client, include_summary=False)
    
            obj.append({
                "file": full_path,
                "code": java_code,
                "classes": current_obj["classes"],
            })
    
    with open("output_obj.json", "w") as f:
        f.write(json.dumps(scan_result))
        
    with open("output_object.json", "w") as f:
        f.write(json.dumps(obj))


if __name__ == '__main__':
    # run(overriding_dir="vulnerableapp")
    openai._utils._logs.logger.setLevel(logging.WARNING)
    openai._utils._logs.httpx_logger.setLevel(logging.WARNING)
    
    parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    parser.add_argument('--dir', type=str, required=True, help='Directory to scan')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    args = parser.parse_args()
    
    method_code = """
private String computeHash(byte[] data) throws NoSuchAlgorithmException {
    MessageDigest digest = MessageDigest.getInstance("SHA-1");
    byte[] encodedhash = digest.digest(data);
    StringBuilder hexString = new StringBuilder(2 * encodedhash.length);
    for (byte b : encodedhash) {
        String hex = Integer.toHexString(0xff & b);
        if(hex.length() == 1) hexString.append('0');
        hexString.append(hex);
    }
    return hexString.toString();
}
    """
    
    calls = parse_method_calls_LLM(method_code, OpenAI(api_key=args.api_key))
    
    for call in calls:
        print(call)
    
    # parser = argparse.ArgumentParser(description='Scan and summarize Java files for vulnerabilities.')
    # parser.add_argument('--api-key', type=str, required=True, help='OpenAI API key')
    # args = parser.parse_args()
    
    # openai_client = OpenAI(api_key=args.api_key)
    
    # with open("vulnerableapp/DBManager.java", 'r') as f:
    #     java_code = f.read()
        
    # file_obj = extract_and_summarize(java_code, openai_client, include_summary=False)
    # print(file_obj) 
    # obj = []
    # obj.append({
    #     "file": "vulnerableapp/DBManager.java",
    #     "code": java_code,
    #     "classes": file_obj["classes"],
    # })
    
    # with open("output_object.json", "w") as f:
    #     f.write(json.dumps(obj))
        
    #tests.test_extract_java_methods()
    
    