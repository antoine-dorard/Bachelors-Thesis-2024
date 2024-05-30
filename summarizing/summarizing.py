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
    pass


def summarize_cluster(cluster: Cluster, openai_client, model="gpt-3.5-turbo"):
    """
    This function uses the OpenAI language model to summarize a cluster of Java methods. 
    It sends the code of each file in the cluster to the model and extracts the summary from the response.
    """
    pass