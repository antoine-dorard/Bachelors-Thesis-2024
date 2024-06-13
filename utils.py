import jsonpickle
import networkx as nx
import matplotlib.pyplot as plt
from warnings import warn


def get_method_signature_tostr(name, return_type, parameters):
    
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

def encode_java_files_to_json(java_files):
    jsonpickle.set_encoder_options('simplejson', sort_keys=True, indent=4)
    return jsonpickle.encode(java_files, unpicklable=False)

def visualize_community_graph(graph, partition, output_file_image):
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
    
def print_clusters(clusters: list):
    for i, cluster in enumerate(clusters):
        print("\nCluster " + str(i) + ":")
        for el in cluster.get_elements():
            print(el)
            