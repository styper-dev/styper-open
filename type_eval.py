import ast, operator, math, os
import operator
import numpy as np 
import logging
import builtins

from styper.SSA.const import  DefIdentObject, ExternalObject 

logger = logging.getLogger(__file__)

def literal_eval(tree, name_val_lookup):

    def checkmath(x, *args):
        if x not in [x for x in dir(math) if not "__" in x]:
            return None
        fun = getattr(math, x)
        return fun(*args)
    
    def check_external_calls(lib_name, x , *args):
        str2lib = {
           # "os":os,  # this cause for process 
            "ast":ast,
            "math":math,
            "re":re,
            "datetime": datetime,
            "time": time 
#            "np": np   
        }

        fun = getattr(str2lib[lib_name], x)
        if all(arg is not None for arg in args):
            return fun(*args)
        return None 

    binOps = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Call: checkmath,
        ast.BinOp: ast.BinOp,
    }

    unOps = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.UnaryOp: ast.UnaryOp,
        ast.Not: operator.__not__,
        ast.Invert:operator.invert
    }

    ops = tuple(binOps) + tuple(unOps)

    def _eval(node):

        if node is None:
            return None 
        if isinstance(node, ast.Name):
            # to look up the local lattice 

            acutal_value = name_val_lookup(node.id)      
            if acutal_value is not None:
                return acutal_value
            return None 
            
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.List):
            # remove nontype values
            return list()
            return list(map(_eval, node.elts))
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            if isinstance(node.left, ops):
                left = _eval(node.left)
            else:
                left = _eval(node.left)
            if isinstance(node.right, ops):
                right = _eval(node.right)
            else:
                right = _eval(node.right)
            
            #TODO!!!!! what if remove this condition checking
            if left is None or right is None:
                return None 
            if isinstance(left, DefIdentObject):
                return None
            if isinstance(right, DefIdentObject):
                return None 

            if type(node.op) in binOps:
                try:
                    return binOps[type(node.op)](left, right)
                except:
                    return None 
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.operand, ops):
                operand = _eval(node.operand)
            else:
                operand = _eval(node.operand)
            if operand is None: 
                return None
            try:  
                return unOps[type(node.op)](operand)
            except:
                return None 

        elif isinstance(node, ast.Call):
        
            if  hasattr(node.func, "id"):
                args = [_eval(x) for x in node.args]
                if all(arg is not None for arg in args):
                    r = checkmath(node.func.id, *args)
                    return r
                return None  
    
            elif isinstance(node.func, ast.Attribute):
                # here is all the functions we can conclude 
                if hasattr(node.func.value, "id"):
                    args = [_eval(x) for x in node.args]   
                    attr_name = node.func.attr 
                    if all(arg is not None for arg in args):
                        try:
                            res = check_external_calls(node.func.value.id, attr_name, *args )
                            return res 
                        except:
                            return None 
                       
                    return None    

       

        elif isinstance(node, ast.JoinedStr):
            elt_vals = [_eval(val) for val in node.values]
            if all (x is not None for x in elt_vals):
                try: 
                    return "".join(elt_vals)
                except:
                    return "<this-is-automated-generated-string>"
            else:
                return None 

        elif isinstance(node, ast.FormattedValue):
            if node.conversion == -1:
                return _eval(node.value)
            else:
                return None 
            #conversion is an integer:
            #- 1: no formatting
            # 115: !s string formatting
            # 114: !r repr formatting
            # 97: !a ascii formatting
        elif isinstance(node, ast.Dict):
            return {}
            return None 
        else:
            return None 
            raise SyntaxError(f"Bad syntax, {type(node)}")
    return _eval(tree)




def _raise_malformed_node(node):
    msg = "malformed node or string"
    if lno := getattr(node, 'lineno', None):
        msg += f' on line {lno}'
    raise ValueError(msg + f': {node!r}')

def _convert_num(node):
    if not isinstance(node, Constant) or type(node.value) not in (int, float, complex):
        _raise_malformed_node(node)
    return node.value
def _convert_signed_num(node):
    if isinstance(node, UnaryOp) and isinstance(node.op, (UAdd, USub)):
        operand = _convert_num(node.operand)
        if isinstance(node.op, UAdd):
            return + operand
        else:
            return - operand
    return _convert_num(node)

def _convert(node):
    if isinstance(node, Constant):
        return node.value
    elif isinstance(node, Tuple):
        return tuple(map(_convert, node.elts))
    elif isinstance(node, List):
        return list(map(_convert, node.elts))
    elif isinstance(node, Set):
        return set(map(_convert, node.elts))
    elif (isinstance(node, Call) and isinstance(node.func, Name) and node.func.id == 'set' and node.args == node.keywords == []):
        return set()
    elif isinstance(node, Dict):
        if len(node.keys) != len(node.values):
            _raise_malformed_node(node)
        return dict(zip(map(_convert, node.keys),
                        map(_convert, node.values)))

    elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        left = _convert_signed_num(node.left)
        right = _convert_num(node.right)
        if isinstance(left, (int, float)) and isinstance(right, complex):
            if isinstance(node.op, Add):
                return left + right
            else:
                return left - right
    return _convert_signed_num(node)

# this is math functions 
MATH_FUNCTIONS = [x for x in dir(math) if not "__" in x]

##  this is built in functions 
BUILT_IN_FUNCTIONS = [x for x in dir(builtins) if not "__" in x]

def type_eval(tree):

    def checkmath(x, *args):
        if x in MATH_FUNCTIONS:
            fun = getattr(math, x)
            #TODO how to evaluate 
            return fun(*args)
    
        if x in BUILT_IN_FUNCTIONS:
            if x == "int":
                return 1
            elif x == "str":
                return "xxx"
            elif x == "float":
                return 1.0
            elif x == "bytes":
                return b'bytes'
            fun = getattr(builtins, x)
            
            return fun(*args) 
        
        

    binOps = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Call: checkmath,  # check all built-in functions 
        ast.BinOp: ast.BinOp,
    }

    unOps = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.UnaryOp: ast.UnaryOp,
        ast.Not: operator.__not__
    }

    ops = tuple(binOps) + tuple(unOps)
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.List):
            return list()
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.value
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            if isinstance(node.left, ops):
                left = _eval(node.left)
            else:
                left = _eval(node.left)
            if isinstance(node.right, ops):
                right = _eval(node.right)
            else:
                right = _eval(node.right)
            if left is not None and right is not None:
                return binOps[type(node.op)](left, right)
            return None

        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.operand, ops):
                operand = _eval(node.operand)
            else:
                operand = _eval(node.operand)
            return unOps[type(node.op)](operand)
        elif isinstance(node, ast.Call) and hasattr(node.func, "id"):
            args = [_eval(x) for x in node.args]
            r = checkmath(node.func.id, *args)
            return r
        else:
            return None
            raise SyntaxError(f"Bad syntax, {type(node)}")

    return _eval(tree)

def src_to_node(src):

    tree = ast.parse(src, mode="eval")
    return tree.body

def test_expr_subsititition():
    from scalpel.typeinfer.visitors import ExprSubstituter
    import astor 
    target = "a"
    new_node = src_to_node("1+1")
    expr_node = src_to_node("a+2")
    expr_sbt = ExprSubstituter(target, new_node)
    new_expr_node = expr_sbt.visit(expr_node)
    print(ast.dump(new_expr_node))
    new_src = astor.to_source(new_expr_node)
    print(new_src)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    #test_expr_subsititition()
    #exit(0)    
    assert type_eval(src_to_node("1+1")) == 2
    assert type_eval(src_to_node("1+-5"))== -4
    assert type_eval(src_to_node("-1")) == -1
    assert type_eval(src_to_node("-+1")) == -1
    assert type_eval(src_to_node("(100*10)+6")) == 1006
    assert type_eval(src_to_node("100*(10+6)")) == 1600
    assert type_eval(src_to_node("2**4")) == 2**4
    assert type_eval(src_to_node("sqrt(16)+1")) == math.sqrt(16) + 1
    assert type_eval(src_to_node("1.2345 * 10")) == 1.2345 * 10
    assert type_eval(src_to_node('"a"*10')) == "aaaaaaaaaa"
    assert type_eval(src_to_node('a*10')) == None
    res =  type_eval(src_to_node("[]+[]"))
    res = type_eval(src_to_node('"a"*3'))
    assert type_eval(src_to_node("[]+[]")) == []
    assert type_eval(src_to_node("[1,2,3] + [1,2,3]")) == []
    assert type_eval(src_to_node('"a"*3')) == "aaa" 
    assert type_eval(src_to_node("int('1000')")) > 0


