from utils import get_method_signature_tostr

class Position:
    def __init__(self, start_line: int, end_line: int, start_column: int, end_column: int) -> None:
        self.start_line = start_line
        self.end_line = end_line
        self.start_column = start_column
        self.end_column = end_column
        
    def to_dict(self):
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_column": self.start_column,
            "end_column": self.end_column
        }
        
    def __str__(self) -> str:
        return "{" + f"Start: {self.start_line}:{self.start_column}, End: {self.end_line}:{self.end_column}" + "}"
    
class JavaParameter:
    def __init__(self, name: str, type_: str) -> None:
        self.name = name
        self.type = type_
        
    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type
        }
        
    def __str__(self) -> str:
        return "{" + f"Name: {self.name}, Type: {self.type}" + "}"
        
        
class JavaMethod:
    def __init__(self, parent, name: str, return_type: str, paremeters: list, position: Position, code: str, summary="") -> None:
        self.name = name
        self.return_type = return_type
        self.position = position
        self.code = code
        self.summary = summary
        self.parent = parent
        
        self.parameters = []
        for p in paremeters:
            if isinstance(p, dict):
                self.parameters.append(JavaParameter(p["name"], p["type"]))
            elif isinstance(p, JavaParameter):
                self.parameters.append(p)
            else:
                raise ValueError("The parameter must be a dictionary or an instance of JavaParameter")
        
        
    def to_dict(self):
        return {
            "name": self.name,
            "signature": get_method_signature_tostr(self.name, self.return_type, self.parameters),
            "position": self.position.to_dict(),
            "code": self.code,
            "summary": self.summary
        }
        
    def __str__(self) -> str:
        # return "{" + f"MethodName: {self.name}, Position: {self.position}, Summary: {self.summary}" + "}"
        return self.parent.name + "." + self.name
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, JavaMethod):
            return False
        if self.name != value.name:
            return False
        if self.return_type != value.return_type:
            return False
        if self.parameters != value.parameters:
            return False
        return True
    
    def __hash__(self) -> int:
        return hash((self.name, self.return_type, tuple(self.parameters)))
    
class JavaClass:
    def __init__(self, name: str, position: Position, code: str, summary="") -> None:
        self.name = name
        self.position = position
        self.code = code
        self.summary = summary
        self.methods = []
        
    def add_new_method(self, name: str, return_type: str, paremeters: list, position: Position, code: str, summary=""):
        self.methods.append(JavaMethod(self, name, return_type, paremeters, position, code, summary))
        
    def add_method(self, method: JavaMethod):
        if not isinstance(method, JavaMethod):
            raise ValueError("The method must be an instance of JavaMethod")
        
        self.methods.append(method)
            
    def add_methods(self, methods: list):
        for m in methods:
            self.add_method(m)
            
    def to_dict(self):
        return {
            "name": self.name,
            "position": {
                "start_line": self.position.start_line,
                "end_line": self.position.end_line,
                "start_column": self.position.start_column,
                "end_column": self.position.end_column
            },
            "code": self.code,
            "summary": self.summary,
            "methods": [m.to_dict() for m in self.methods]
        }
        
    def __str__(self) -> str:
        return "{" + f"ClassName: {self.name}, Position: {self.position}, Summary: {self.summary}, Methods: {self.methods}" + "}"
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, JavaClass):
            return False
        if self.name != value.name:
            return False
        if self.methods != value.methods:
            return False
        return True
    
    def __hash__(self) -> int:
        return hash((self.name, tuple(self.methods)))
    
class JavaFile:
    def __init__(self, path: str, code: str, classes: list) -> None:
        self.path = path
        self.code = code
        self.classes = []
        
        for c in classes:
            if isinstance(c, JavaClass):
                self.classes.append(c)
            else:
                raise ValueError("The class must be an instance of JavaClass")
        
    def add_new_class(self, name, position) -> None:
        self.classes.append(JavaClass(name, position))
        
    def add_class(self, class_: JavaClass) -> None:
        if not isinstance(class_, JavaClass):
            raise ValueError("The class must be an instance of JavaClass")
        
        self.classes.append(class_)
            
    def add_classes(self, classes: list) -> None:
        for c in classes:
            self.add_class(c)
        
    def get_class(self, name) -> JavaClass:
        for c in self.classes:
            if c.name == name:
                return c
            
        return None
    
    def get_code(self):
        return self.code
    
    def to_dict(self):
        return {
            "path": self.path,
            "code": self.code,
            "classes": [c.to_dict() for c in self.classes]
        }
    
    def __str__(self) -> str:
        return "{" + f"Path: {self.path}, Classes: {self.classes}" + "}"

    
# TODO create interface for clustering and  for cluster. The clustering class should return an instance of the cluster class.
# It should contain all getters (and setters) so that the person who implements the interface knows what to return.
# Path: clustering.py
