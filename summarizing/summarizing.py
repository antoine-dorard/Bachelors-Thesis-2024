from openai import OpenAI

from clustering.clustering import Cluster
from warnings import warn

def summarize(code, openai_client, model="gpt-3.5-turbo"):
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
    # TODO also try chain of thoughts approach (give one method after the other and then summarize the cluster)
    
    code = ""
    
    for method in cluster.get_elements():
        code += f" ```{method.code}```\n\n"
    
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": code}
        ]
    )
    
    return response.choices[0].message.content
    