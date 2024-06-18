from openai import OpenAI
import tiktoken

from clustering.clustering import Cluster
from warnings import warn

model_context = {
    "gpt-3.5-turbo": {
        "context": 16385,
        "max_out": 4096
    },
    "gpt-3.5-turbo-0125": {
        "context": 16385,
        "max_out": 4096
    },
    "gpt-3.5-turbo-0301": {
        "context": 4097,
        "max_out": 4097
    },
    "gpt-3.5-turbo-0613": {
        "context": 4097,
        "max_out": 4097
    },
    "gpt-3.5-turbo-1106": {
        "context": 16385,
        "max_out": 4096
    },
    "gpt-3.5-turbo-16k": {
        "context": 16385,
        "max_out": 16385
    },
    "gpt-3.5-turbo-16k-0613": {
        "context": 16385,
        "max_out": 16385
    },
    "gpt-4": {
        "context": 8192,
        "max_out": 8192
    },
    "gpt-4-0125-preview": {
        "context": 128000,
        "max_out": 4096
    },
    "gpt-4-0314": {
        "context": 8192,
        "max_out": 8192
    },
    "gpt-4-0613": {
        "context": 8192,
        "max_out": 8192
    },
    "gpt-4-1106-preview": {
        "context": 128000,
        "max_out": 4096
    },
    "gpt-4-1106-vision-preview": {
        "context": 128000,
        "max_out": 4096
    },
    "gpt-4-32k": {
        "context": 32768,
        "max_out": 32768
    },
    "gpt-4-32k-0314": {
        "context": 32768,
        "max_out": 32768
    },
    "gpt-4-32k-0613": {
        "context": 32768,
        "max_out": 32768
    },
    "gpt-4-turbo-preview": {
        "context": 128000,
        "max_out": 4096
    },
    "gpt-4-vision-preview": {
        "context": 128000,
        "max_out": 4096
    },
    "gpt-4o": {
        "context": 128000,
        "max_out": None
    },
    "gpt-4o-2024-05-13": {
        "context": 128000,
        "max_out": None
    },
}

def summarize(code, openai_client, model="gpt-3.5-turbo"):
    """
    DEPRECATED - Old prompt for summarizing Java code. Use summarize_code or summarize_cluster instead.
    """
    warn("This function is deprecated. Use summarize_code or summarize_cluster instead.", DeprecationWarning, stacklevel=2)
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


def summarize_code(code: str, openai_client, model="gpt-3.5-turbo"):
    """
    This function uses the OpenAI language model to summarize Java code. 
    It sends the code to the model and extracts the summary from the response.
    """
    system_message = """
You are a professional Java code interpreter. Your role is to summarize code while strictly following the two following main rules:
1. PRECISENESS: Always be as precise as possible. You must include everything relevant.
2. CONCISENESS: always keep the summary concise, while not breaking the first rule.

You may be given to interpret entire Java files, classes, or only methods.
If you are given a file, do not explain the details for each method. The summary should be a high-level overview of the file's purpose and functionality and not a line-by-line or method by method explanation.

Provide a ONE SENTENCE summary of the provided piece of code, keeping in mind that the sentence must tell the reader what the piece of code does overall.
    """
    
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": code}
        ]
    )
    return response.choices[0].message.content


def summarize_cluster(cluster: Cluster, openai_client, model="gpt-3.5-turbo"):
    """
    This function uses the OpenAI language model to summarize a cluster of Java methods. 
    It sends the code of each file in the cluster to the model and extracts the summary from the response.
    """
    system_message = """
You are a professional Java code interpreter. Your role is to summarize a cluster of java methods. In other words,
you must provide a high-level overview of the functionality of the methods in the cluster, and what they acheive in the context of the cluster.
Keep the following rules in mind:
1. PRECISENESS: Always be as precise as possible. You must include everything relevant.
2. CONCISENESS: always keep the summary concise, while not breaking the first rule.

Provide a ONE SENTENCE summary of the cluster, keeping in mind that the sentence must tell the reader what the provided group of methods do.
    """
    
    code = ""
    
    for method in cluster.get_elements():
        code += f" ```{method.code}```\n\n"
    
    
    enc = tiktoken.encoding_for_model("gpt-4o")
    if model_context.get(model) is None:
        raise ValueError(f"Model {model} is not supported.")
    
    if len(enc.encode(code)) > model_context.get(model).get("context"):
        warn("The code is too long to be summarized by the model. The summary may not be accurate.")
        return "Cluster too large"
    
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": code}
        ]
    )
    
    return response.choices[0].message.content
    