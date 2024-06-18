import jsonpickle
import networkx as nx
import matplotlib.pyplot as plt
from warnings import warn
from typing import Union, Any


def get_method_signature_tostr(name: str, return_type: Union[str, Any], parameters: list) -> str:
    """
    Constructs the method signature as a string.

    Parameters
    name (str): The name of the method.
    return_type (Union[str, Any]): The return type of the method
    parameters (list): A list of parameters, each containing 'type' and 'name' attributes.

    Returns
    str: The string representation of the method signature.
    """
    signature = ""
    if return_type:
        if isinstance(return_type, str):
            signature += return_type + " "
        else:
            signature += return_type.name + " "
    else:
        signature += "void "
        
    signature += name + "("
    
    for i, param in enumerate(parameters):
        param_type = param.type if isinstance(param.type, str) else param.type.name
        signature += param_type + " " + param.name
        if i < len(parameters) - 1:
            signature += ", "
            
    signature += ")"
    
    return signature

def encode_java_files_to_json(java_files: list) -> (Any | None):
    """
    Encodes a list of Java files to a JSON string using jsonpickle.

    Parameters
    java_files (list): A list of Java file objects to be encoded.

    Returns
    A JSON representation of the Java files.
    """
    jsonpickle.set_encoder_options('simplejson', sort_keys=True, indent=4)
    return jsonpickle.encode(java_files, unpicklable=False)

def visualize_community_graph(graph: nx.Graph, partition: dict, output_file_image: str) -> None:
    """
    Visualizes the community structure of a graph and saves the image to a file.

    Parameters
    graph (networkx.Graph): The graph to be visualized.
    partition (dict): A dictionary where keys are node identifiers and values are the community index.
    output_file_image (str): The file path to save the visualization image.

    Returns
    None
    """
    if len(partition) == 0:
        warn("The partition is empty. The graph will not be rendered.")
        return
    
    plt.clf()
    pos = nx.spring_layout(graph)
    cmap = plt.get_cmap('viridis', max(partition.values()) + 1)
    nx.draw_networkx_nodes(graph, pos, partition.keys(), node_size=500, cmap=cmap, node_color=list(partition.values()), alpha=0.6)
    nx.draw_networkx_edges(graph, pos, alpha=0.5)
    nx.draw_networkx_labels(graph, pos, font_size=10)
    plt.savefig(output_file_image)
    
def print_clusters(clusters: list) -> None:
    """
    Prints the elements of each cluster.

    Parameters
    clusters (list): A list of cluster objects, each having a method get_elements() that returns the elements of the cluster.

    Returns
    None
    """
    for i, cluster in enumerate(clusters):
        print("\nCluster " + str(i) + ":")
        for el in cluster.get_elements():
            print(el)
            