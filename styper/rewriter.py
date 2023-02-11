import os
import sys
import ast

class Rewriter(ast.NodeTransformer):
    #def __init__(self,src, pattern, new_stmt):
    def __init__(self, src):
        # pattern
#        self.pattern = pattern
#        self.new_stmt = new_stmt
        self.src = src
        self.ast = None
        self.ast = ast.parse(self.src, mode='exec')

    def search_for_pos(self, stmt_lst, pattern): 
        for i, stmt in enumerate(stmt_lst):
            if pattern(stmt):
                return i
        return -1

    def rewrite(self):
        self.generic_visit(self.ast)
       
        return ast.fix_missing_locations(self.ast)

    # once or all 
    def insert(self):
        assert self.ast is not None
        assert isinstance(self.ast, ast.Module)
        self.insert_after()
    # once or all

    def insert_before(self, loc=""):
        assert self.ast is not None
        assert isinstance(self.ast, ast.Module)
        pos = self.search_for_pos(self.ast.body, self.pattern)
        if pos<0:
            return self.ast

        call_node = ast.Call(ast.Name(id='print',ctx=ast.Load()),
                [ast.Constant("testing", None)], [])
        new_stmt = ast.Expr(call_node)

        self.ast.body.insert(pos, new_stmt)
        self.ast = ast.fix_missing_locations(self.ast)
        return self.ast

    def insert_after(self):
        assert self.ast is not None
        assert isinstance(self.ast, ast.Module)
        pos = self.search_for_pos(self.ast.body, self.pattern)
        new_stmt = ast.Call(ast.Name(id='print',ctx=ast.Load()),
                [ast.Name(id="testing", ctx=ast.Load())], [])
        self.ast.body.insert(pos+1, new_stmt)
        self.ast =  ast.fix_missing_locations(self.ast)

    def remove(self):
        assert self.ast is not None
        assert isinstance(self.ast, ast.Module)
        pos = self.search_for_pos(self.ast.body, self.pattern)
        if pos<0:
            return self.ast
        del self.ast.body[pos] 
        self.ast =  ast.fix_missing_locations(self.ast)
        return self.ast

    def replace(self):
        assert self.ast is not None
        assert isinstance(self.ast, ast.Module)
        pos = self.search_for_pos(self.ast.body, self.pattern)
        if pos<0:
            return self.ast
        call_node = ast.Call(ast.Name(id='print',ctx=ast.Load()),
                [ast.Constant("testing1", None)], [])
        new_stmt = ast.Expr(call_node)
        self.ast.body[pos] = new_stmt
        return ast.fix_missing_locations(self.ast)

    def visit_Name(self, node):
        #if node.id in self.pattern['Name']:
        #    new_name = self.pattern['Name'][node.id]
        #    node.id = new_name
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        return node
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        return node

    def get_func_name(self, node):
        if hasattr(node, "id"):
            return node.id
        elif hasattr(node,"attr"):
            return self.get_func_name(node.value)+"."+node.attr
        else:
            pass

    def visit_Call(self, node):
        func_name = self.get_func_name(node.func)
        #if func_name in self.pattern["Call"]:
        #    new_func_name = self.pattern["Call"][func_name]
        #    if new_func_name is None:
        #        return None
        #    node.func.id = new_func_name


        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        return node

    def visit_Return(self, node):
        self.generic_visit(node)
        return node

    def visit_Delete(self, node):
        self.generic_visit(node)
        return node

    def visit_Assign(self, node):
        # to rewrite

        if len(node.targets) ==1 and isinstance(node.value, ast.Lambda):
            if isinstance(node.targets[0], ast.Name):
                fun_name = node.targets[0].id
                return_stmt = ast.Return(node.value.body)
                body_stmts = [return_stmt]
                decorator_list = []
                return ast.FunctionDef(fun_name, node.value.args, body_stmts, decorator_list)

        if len(node.targets) ==1 and isinstance(node.value, ast.ListComp):
            print(ast.dump(node.value))

            iter = node.value.generators[0].iter
            ifs  = node.value.generators[0].ifs
            target_name = node.value.generators[0].target.id
            target = ast.Name(id=target_name, ctx=ast.Store())

            orelse = []
            new_lst_name = "_hidden_" + node.targets[0].id
            if len(ifs) == 0:
                append_attr = ast.Attribute(value=ast.Name(id=new_lst_name, ctx=ast.Load()),attr='append', ctx=ast.Load())  
                append_call = ast.Call(append_attr, [node.value.elt], [])
                append_stmt = ast.Expr(append_call)
                body_stmts = [append_stmt]
            else:
                append_attr = ast.Attribute(value=ast.Name(id=new_lst_name, ctx=ast.Load()),attr='append', ctx=ast.Load())  
                append_call = ast.Call(append_attr, [node.value.elt], [])
                append_stmt = ast.Expr(append_call)
                if_body_stmts = [append_stmt]
                if_stmt = ast.If(ifs[0], if_body_stmts, [])
                body_stmts = [if_stmt]
                pass
            return ast.For(target, iter, body_stmts, orelse)
        self.generic_visit(node)
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node):
        self.generic_visit(node)
        return node

    def visit_For(self, node):
        self.generic_visit(node)
        return node

    def visit_AsyncFor(self, node):
        self.generic_visit(node)
        return node

    def visit_While(self, node):
        self.generic_visit(node)
        return node


    def visit_If(self, node): 
        #if "if" in self.pattern["Stmt"]:
        #    alt_stmt = self.pattern["Stmt"]["if"]
        #    if alt_stmt is None:
        #        return None

        self.generic_visit(node)

        return node
    def visit_IfExp(self, node): 
        #if "if" in self.pattern["Stmt"]:
        #    alt_stmt = self.pattern["Stmt"]["if"]
        #    if alt_stmt is None:
        #        return None
        self.generic_visit(node)
        return node
    def visit_With(self, node):
        self.generic_visit(node)
        return node

    def visit_AsyncWith(self, node):
        self.generic_visit(node)
        return node

    def visit_Raise(self, node):
        self.generic_visit(node)
        return node

    def visit_Try(self, node):
        self.generic_visit(node)
        return node
    def visit_Assert(self, node):
        self.generic_visit(node)
        return node
    def visit_Import(self, node):
        self.generic_visit(node)
        return node
    def visit_ImportFrom(self, node):
        self.generic_visit(node)
        return node
    def visit_Global(self, node):
        self.generic_visit(node)
        return node
    def visit_Nonlocal(self, node):
        self.generic_visit(node)
        return node
    def visit_Expr(self, node):
        self.generic_visit(node)
        return node
    def visit_Pass(self, node):
        self.generic_visit(node)
        return node
    def visit_Break(self, node):
        self.generic_visit(node)
        return node
    def visit_Continue(self, node):
        self.generic_visit(node)
        return node

