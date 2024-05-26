import javalang
import jsonpickle

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