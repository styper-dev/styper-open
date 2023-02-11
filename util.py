from functools import reduce
from unicodedata import numeric
import networkx as nx
import sys
import random
import ast
import re 
random.seed(500)

"""
https://arxiv.org/pdf/2105.03595.pdf
boolean operations
blop  :== AND | OR | Not

numeric operations
numop := Add|Sub|Mult|Div|Mod|UAdd|USub

bitwise operations

bitop := LShift | RShift|BitOr|BitAnd|BitXor|FlloorDiv|Invert
compare operations
cmpop := Eq|NotEq|Lt|LtE|Gt|GtE|Is|IsNot|In|NotIn

"""

boolean_op = [ast.And(), ast.Or(), ast.Not()]
numeric_op = [ast.Add(), ast.Sub(), ast.Mult(), ast.Div(), ast.Mod(), ast.UAdd(), ast.USub()]
bit_op = [ast.LShift(), ast.RShift(), ast.BitOr(), ast.BitAnd(), ast.BitXor(), ast.FloorDiv(), ast.Invert()]
cmp_op = [ast.Eq(), ast.NotEq(), ast.Lt(), ast.LtE(), ast.Gt(), ast.GtE(), ast.Is(), ast.IsNot(), ast.In(), ast.NotIn()]


def is_class_name(s:str) -> bool:
    """ 
    Determines whether a string is written in camel case

    :param s: The string to check
    :return: True if the string is camel case, False otherwise
    """
    if len(s.split("."))>1:
        return False
    pattern = '([A-Z][a-z]*)+'
    if re.search(pattern, s):
        return True
    return False


def get_attr_name (node):
    if isinstance(node, ast.Call):
        # to be test
        return get_attr_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        attr_name = get_attr_name(node.value)
        
        return attr_name +"."+node.attr
    elif isinstance(node, ast.Subscript):
        return get_attr_name(node.value)
    else:
        # such as (a**2).sum()
        return ""

built_in_func_type = {

    "abs": float,
    "bytearray":bytearray,
    "bytes":bytes,
    "complex":complex,
    
    
    "divmod": tuple,
    "enumerate":enumerate,
    "filter":filter,  
    "float":float,
    "frozenset":frozenset,
    
    "hasattr":bool,
    "all": bool,
    "any": bool,
    "bool":bool,
    "isinstance":bool,
    "issubclass":bool,
    "callable":bool,

    "id":int,
    "int":int,
    "len":int,
    "round":int,

    "list":list,
    "sorted":list,
    "dir":list,
    
    "locals":dict,
    "vars":dict,
    "globals":dict,
    "dict":dict,

    "map": "Iterator",
    "memoryview":memoryview,
    "object":object,
    
    "range":range,
    "str":str,
    "repr":str,
    "oct":str,
    "ord":str,
    "hash":int,
    "hex":str,
    "repr":str,
    "chr":str,
    "ascii": str,
    "bin":str,
    "set":set,
    "slice":slice,
    "tuple":tuple,
    "zip":"Iterator", 
    "iter":"Iterator",
    "reversed":"Iterator"
}

Gamma_types = ["int" , "float",  "str" ,  "bool" ,  "bytes"]

def rule_mult(theta1, theta2):

    # Mult rule applied: {int, bool} numop {\Gamma, List, Tuple, O} -> \theta in {\Gamma, List, Tuple, O}  
    if theta1 in ["List", "tuple"] + Gamma_types:
        if theta2 in ["bool", "int"]:
            return theta1
    
    if theta2 in ["List", "tuple"] + Gamma_types:
        if theta1 in ["bool", "int"]:
            return theta2

    return any.__name__

def rule_sub(theta1, theta2):

    # Sub rule applied:  \pi \vdash: e_1: \theta_1  \pi \vdash e_2: \theta_2   theta \in {\Gamma, Set, O}
    # ->    \theta \cap 

    if theta1 in ["Set"] + Gamma_types:
        return theta1
    
    
    if theta1 in ["Set"] + Gamma_types:
        return theta1
    return any.__name__
    
    pass 
def get_type_from_expr(node, imports=None) -> str:
    """
    Get the type of a node

    :param node: The node to get the type of
    :param imports: Dictionary of known imported types
    :return: The type of the node
    """
    if node is None:
        return any.__name__
    elif isinstance(node, str) and node[0:3] == "org":
        return node[4:]
    elif isinstance(node, ast.BoolOp):
        return "bool"
    elif isinstance(node, ast.cmpop):
        return "bool"
    elif isinstance(node, ast.Compare):
        return "bool"
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return "bool"
    elif isinstance(node, ast.BinOp):
        left_type = get_type_from_expr(node.left)
        right_type = get_type_from_expr(node.right)
        
        if isinstance(node.op, ast.Mult):
            return rule_mult(left_type, right_type)
        elif isinstance(node.op, ast.Sub):
            return rule_sub(left_type, right_type)
            
        
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant) and isinstance(node.left, ast.Str):
            return "str"
        elif isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Name) and isinstance(node.right, ast.Dict):
            return "str"
        
        elif isinstance(node.op, ast.Add):
            if isinstance(node.left, (ast.Constant, ast.Num, ast.List, ast.ListComp,
                                      ast.Set, ast.SetComp, ast.Dict, ast.DictComp)):
                
                return get_type_from_expr(node.left)

            if isinstance(node.right, (ast.Constant, ast.Num, ast.List, ast.ListComp,
                                       ast.Set, ast.SetComp, ast.Dict, ast.DictComp)):
                
                return get_type_from_expr(node.right)
            
            #print(left_type, right_type, '!!!!')
            if left_type not in ["any", "call"]:
                return left_type
            if right_type not in ["any", "call"]:
                return right_type
            return any.__name__
    
    if isinstance(node, ast.Constant):
        if node.value is None:
            return "Optional"
        return type(node.value).__name__  

    elif isinstance(node, ast.List) or isinstance(node, ast.Tuple):
        return type(node).__name__ 
    elif isinstance(node, ast.Dict):
        # TODO
        return  "Dict"
    elif isinstance(node, (ast.Set, ast.SetComp)):
        return  set.__name__
    elif isinstance(node, ast.Str):
        return str.__name__
    elif isinstance(node, ast.JoinedStr):
        return str.__name__
    
    elif isinstance(node, ast.NameConstant):
        return any.__name__
    elif isinstance(node, ast.Lambda):
        return "Callable"
    elif isinstance(node, ast.DictComp):
        return dict.__name__
    elif isinstance(node, ast.ListComp):
        return list.__name__
    elif isinstance(node, ast.GeneratorExp):
        return "generator"
    elif isinstance(node, ast.Call):
        # Check to see if it is an imported callable
        if isinstance(node.func, ast.Name):
            if node.func.id in built_in_func_type:
                ret_type = built_in_func_type[node.func.id]
                if type(ret_type) == str:
                    return ret_type
                else:
                    return ret_type.__name__
            else:
                return "call"
        elif type(node.func) == ast.Attribute:
            # this is something like "".join(etls)
             call_name = get_attr_name(node.func)
             if type(node.func.value) == ast.Constant and node.func.attr == "join":
                 return str.__name__
             elif type(node.func.value) == ast.Constant and node.func.attr == "format":
                 return str.__name__
                    
             elif is_class_name(call_name):
                 return call_name    
             return "call"
        else:
            
            return "call"
        
    elif isinstance(node, bool):
        return bool.__name__
    else:
        return any.__name__


def read_data(fn):
    lines = open(fn).readlines()
    lines = [line.strip().split()[1] for line in lines]
    lines = [line.split('/')[-1] for line in lines]
    return lines
def count_unqiue():
    fn = sys.argv[1]
    lines = open(fn).readlines()
    print(len(lines))
    lines = set(lines)
    for line in lines:
        print(line.strip())

def unique_repo():
    fn = sys.argv[1]
    lines = open(fn).readlines()
    all_repo_names = []
    for line in lines:
        parts = line.split(',')
        repo_str = parts[1].split('/')[-1]
        repo_name  = "-".join(repo_str.split('-')[1:-1])
        all_repo_names.append(repo_name)
    all_repo_names = list(set(all_repo_names))
    print("\n".join(all_repo_names))

def sample():
    fn = sys.argv[1]
    all_lines = open(fn).readlines()
    all_lines = list(all_lines)
    k = 20
    sample_lines = random.choices(all_lines, k=20)
    for line in sample_lines:
        #print(line.strip().split(',')[2])
        print(line.strip())



def main():
    fn1 = sys.argv[1]
    fn2 = sys.argv[2]
    lines1 = read_data(fn1)
    lines2 = read_data(fn2)
    for line in lines2:
        if line not in lines1:
            print(line.strip()) 

if __name__ == '__main__':
    #main()
    #count_unqiue()
    #unique_repo()
    sample()
    #filter_repo_error()
    #is_nameerror_reduce()
