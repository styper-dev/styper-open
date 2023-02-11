import sys
import ast


def read_from_func_def(fundef_node):
    # this one has no suffix of <arg>
    type_info = {}
    type_info["<ret>"] = fundef_node.returns 
    for arg in fundef_node.args.args:
        if arg.annotation is not None:
            type_info[arg.arg] = arg.annotation
    for stmt in fundef_node.body:
        if not isinstance(stmt, ast.AnnAssign):
            continue 
        if hasattr(stmt.target, "id") and stmt.annotation is not None:
            type_info[stmt.target.id] = stmt.annotation
      
    return type_info

def read_from_func_def_fn(fundef_node):
    type_info = {}
    type_info["<ret>"] = fundef_node.returns 
    for arg in fundef_node.args.args:
        if arg.annotation is not None:
            type_info["<arg>."+arg.arg] = arg.annotation
    for stmt in fundef_node.body:
        if not isinstance(stmt, ast.AnnAssign):
            continue 
        if hasattr(stmt.target, "id") and stmt.annotation is not None:
            type_info[stmt.target.id] = stmt.annotation      
    return type_info


def read_stub_full(ast_tree):
    n_returns = 0
    fun_name_lst = []
    shed_type_dict = {}
    arg_type_dict = {}
    for stmt in ast_tree.body:
        if type(stmt) == ast.FunctionDef:
            shed_type_dict[stmt.name] = read_from_func_def_fn(stmt)
        elif type(stmt) == ast.ClassDef:
            class_name = stmt.name
            for  c_stmt in stmt.body:
                if isinstance(c_stmt, ast.FunctionDef):
                    shed_type_dict[class_name+"."+c_stmt.name] = read_from_func_def_fn(c_stmt)

    return shed_type_dict

def read_stub_types(ast_tree):
    n_returns = 0
    fun_name_lst = []
    shed_type_dict = {}
    arg_type_dict = {}
    for stmt in ast_tree.body:
        if type(stmt) == ast.FunctionDef:
            shed_type_dict[stmt.name] = read_from_func_def(stmt)
        elif type(stmt) == ast.ClassDef:
            class_name = stmt.name
            for  c_stmt in stmt.body:
                if isinstance(c_stmt, ast.FunctionDef):
                    shed_type_dict[class_name+"."+c_stmt.name] = read_from_func_def(c_stmt)

    #return n_returns, fun_name_lst
    return shed_type_dict

def read_stub_types_fine_grained(ast_tree):
    n_returns = 0
    fun_name_lst = []
    shed_type_dict = {}
    arg_type_dict = {}
    for stmt in ast_tree.body:
        if type(stmt) == ast.FunctionDef:
            shed_type_dict[stmt.name] = read_from_func_def_fn(stmt)
        elif type(stmt) == ast.ClassDef:
            class_name = stmt.name
            for  c_stmt in stmt.body:
                if isinstance(c_stmt, ast.FunctionDef):
                    shed_type_dict[class_name+"."+c_stmt.name] = read_from_func_def_fn(c_stmt)

    return shed_type_dict

def main():
    filename = "top-10/.pyre/types/requests/tmp/requests/utils.pyi"
    #filename = sys.argv[1]
    code = open(filename).read()
    ast_tree = ast.parse(code)
    type_dict = read_stub_types(ast_tree)
    n_fun_all = 0
    for k, v in type_dict.items():
        if v is None:
            continue
        if hasattr(v, "id") and v.id == "Any":
            continue
        if type(v) == ast.Constant and v.value == None:
            continue


        n_fun_all += 1

    print(n_fun_all)

    return 0

if __name__ == "__main__":
    main()
