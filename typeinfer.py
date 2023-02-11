from multiprocessing import Pool
from typing import Optional

import os
import sys
import ast 
import re 

# external lib needed 
from attr import Attribute, attr, has
import numpy as np 

import  astor
from regex import E
from match import match_types, invalid_type_annotations

from styper.cfg import CFGBuilder
from styper.SSA.const import SSA, DefIdentObject, ExternalObject, TypeObject 
from styper.typeinfer.visitors import ExprSubstituter,CallTypeHints
from read_stub import read_stub_types
from read_stub import read_from_func_def
from type_eval import literal_eval
from util import get_type_from_expr, get_attr_name, sample
from typeshed_test import load_typeshed_cache

typeshed_cache = load_typeshed_cache()
from styper.import_graph.file_system import FileSystem


# when def-use, no scope gives out
DEFONLY= False 
DEFUSEONLY = False
ENFORCE_USER_TYPE = True



class TempObject(object):
    def __init__(self, name):
        self.cls_name = name
    def __str__(self) -> str:
        return self.cls_name
    
    def get_type(self):
        return self.cls_name


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



class TypeLink:
    def __init__(self, name, scope):
        self.name = name
        self.scope = scope 

 
class CCPLattice:
    def __init__(self):
  
        self.values = {}
        self.exprs = {}
        self.types = {}  
        self.typelinks = {}
        self.scope_name = None
        self.sg  = None 
        # TOP T  lower T and any other constants
        self.value = "TOP_T"

    def add_var(self, name, value="TOP_T"):
        self.values[name] = value 
        self.types[name] = self.get_type(value)
        self.exprs[name] = None 
    
    
    def set_scope(self, scope_name):
        self.scope_name = scope_name
    
    def update_value(self, name, value):
        if value is None:
            self.values[name] = "TOP_T"
        else:
            self.values[name] = value
            self.types[name] = self.get_type(value)

    def update_type(self, name, type_name):
        self.types[name] = type_name 
    
    def update_expr(self, name, expr):
        self.exprs[name] = expr 
    
    def get_expr(self, name):
        for (ident_name, no), expr in self.exprs.items():
            if ident_name == name and expr is not None:
                return expr 
        return None 


    def get_type(self, value):

        if type(value) == str and value == "TOP_T":
            return None 

        if isinstance(value, (DefIdentObject, TempObject, TypeObject)):
            return value.get_type()
        elif isinstance(value, ExternalObject):
            if is_class_name(value.imported_name):
                return value.imported_name
            else:
                return None 
        return type(value).__name__
    
    def get_value(self, name):
        if name in self.values:
            return self.values[name]
        return None  
    
    def get_types(self):
        type_dict = {}
        for key, type_name in self.types.items():
            if type_name is None or type_name is None:
                 
               type_name = get_type_from_expr(self.exprs[key]) 
               call_name = get_attr_name(self.exprs[key])

               if type_name == "call" :
                   if call_name in typeshed_cache:      
                        type_name = typeshed_cache[call_name]
            
            # failed to infer 
            if type_name in invalid_type_annotations:
                type_name = "any"
                 
            if key[0] not in type_dict:
                type_dict[key[0]] = set()

            if type(type_name) == list:
                type_dict[key[0]].update(type_name)
            else: 
                type_dict[key[0]].add(type_name)

        type_dict_final = {}
        for var_name, type_names in type_dict.items():
          
            type_names = list(type_names)
            is_optional = "Optional" in type_names
            
            type_names = [x for x in type_names if x != "any" and x!="NoneType" and x!="Optional" and x is not None]

            if len(type_names) == 0:
                if is_optional:
                    type_name_str = "Optional"
                else:
                    type_name_str = "any"
                type_dict_final[var_name] = type_name_str
                continue  
        
            if len(type_names) == 1:
                type_name_str = type_names[0]            
            elif len(type_names)>1:
                type_name_str = ",".join(type_names)
                type_name_str = f"Union[{type_name_str}]"
            
            if is_optional:
                #print("testing", type_name_str, var_name)
                type_name_str = f"Optional[{type_name_str}]"
                #print(type_name_str, var_name)
            

            type_dict_final[var_name] = type_name_str
        
        return type_dict_final

    def get_value_by_name(self, name):

        # now we disable to lookup all the values.
        # we only look at the last value.
        # the trick here is to use the first value :
        # this is flow insensitive 
        #val =  self.values.get((name,0))
        #if type(val) != str:
        #    return val 
        #if val != "TOP_T":
        #    return val 
        #return None 
        #####################
        # disable def-use relations 
        #if DEFONLY == False:
        #    return None 

        for key, val in self.values.items():
            #if key[0] == "out":
            #   # print(val)
            if key[0] == name:
                if type(val)!=str:
                    return val
                if  val != "TOP_T":
                    return val 
               
        return None  
    
    def add_type_link(self, ident_name, no, func_name, scope_name=None):
        self.typelinks[(ident_name,no)] = (func_name, scope_name)
    
    def get_type_links(self):
        return self.typelinks
    
    
    def print_values(self):
        print("-------------", self.scope_name, "-----------------")
        print("values:")
        for name, val in self.values.items():
            print(name, val)
        #print("Type links:")
        
        #for name,val in self.typelinks.items():
        #    print(name, val)
    

class TypeInference:

    def __init__(self, entry_point):
        self.entry_point = entry_point
        self.mod_lattice = {}
        self.scope_args = {}

        self.leaves = []

        # Build graph of the directory
        self.entry_point = entry_point
        self.import_graph = None 

        
        self.import_graph = FileSystem(self.entry_point)
        self.import_graph.build_dir_tree()
        self.leaves = self.import_graph.get_leaf_nodes()
        
        self.external_type_links = {}
          

    def query_value(self, ident_name, cur_scope_name, mod_lattice, target_scope_name=None):

        #if DEFONLY:
        #    return None 
   
        target_scope = self.sg.name_lookup(ident_name, cur_scope_name)
        
        
        if target_scope is None:
            return None
        
        if target_scope not in mod_lattice:
            return None 

        # disable name resolution
        if DEFUSEONLY and target_scope_name != cur_scope_name:
            
            return None 
        return mod_lattice[target_scope].get_value_by_name(ident_name)
    

        pass 
    def lookup_scope_name(self, cur_scope_name:str, target_scope_name:str, mod_lattice):
        # locate a scope  from enclosing scopes
        if target_scope_name in mod_lattice:
            return target_scope_name
        enclosing_scope_parts =  cur_scope_name.split(".")
        n_depth = len(enclosing_scope_parts)
       
        for i in range(1, n_depth):
            parent_scope_name= ".".join(enclosing_scope_parts[0: n_depth-i])
            tmp_scope_name = parent_scope_name + "."+target_scope_name
            if tmp_scope_name in mod_lattice:
                return tmp_scope_name
       
        return None 


    def restore_obj_acess(self, obj_name, working_scope_name, mod_lattice):
        # to locate up the attribute function calls or attribute access
        assigned_obj = self.query_value(obj_name, working_scope_name, mod_lattice)
        return assigned_obj    

        #if isinstance(assigned_obj, DefIdentObject):
        #    return assigned_obj.name
        #if isinstance(assigned_obj, TempObject):
        #    return assigned_obj.cls_name
    
    def type_infer(self, const_dict, working_scope_name, parent_scope_name=None, is_inside_class=False):

        def get_func(node):
            if type(node) == ast.Name:
                return node.id
            elif type(node) == ast.Constant:
                # ingore such as  "this is a constant".join()
                return ""
            elif type(node) == ast.BinOp:
                # ingore such as  (a+b+c).fun()
                return ""
            elif type(node) == ast.JoinedStr:
                return "" 
            elif type(node) == ast.Dict:
                return "" 
            elif type(node) == ast.Compare:
                return ""
            elif type(node) == ast.ListComp:
                return ""
            elif type(node) == ast.List:
                return ""
            elif type(node)  == ast.SetComp:
                return ""
            elif type(node)  == ast.DictComp:
                return ""
            elif type(node)  == ast.Set:
                return ""
            elif type(node) == ast.Await:
                return ""
            elif type(node) == ast.IfExp:
                return ""
            elif type(node) == ast.BoolOp:
                return ""
            elif type(node) == ast.Tuple:
                return ""
            elif type(node) == ast.UnaryOp:
                return ""
            elif type(node) == ast.Lambda:
                return ""
            elif type(node) == ast.Subscript:
                # currently, we will ignore the slices because we cannot track the type of the value.
                # for instance,  a[something].fun() ->  a.fun()
                # this sacrifice
                return get_func(node.value)  
            elif type(node) == ast.Attribute:
                return get_func(node.value) + "." + node.attr 
            elif type(node) == ast.Call:
                return get_func(node.func)
            else:
                raise Exception(str(type(node)))
        
        for (ident_name, ident_no), value_expr in const_dict.items():
            if value_expr is None:
                continue 
            #print(ident_name, type(value_expr))
          
            if isinstance(value_expr, ast.IfExp):
               value_expr = value_expr.body 
            
            # alias anayis here 
            if isinstance(value_expr, ast.Name):
                # this is an argument 
                if (value_expr.id, -1) in const_dict:
                    value_expr = const_dict[(value_expr.id, -1)]
                elif (value_expr.id, 0) in const_dict:
                    value_expr = const_dict[(value_expr.id, 0)]
                    
            self.mod_lattice[working_scope_name].add_var((ident_name,ident_no))          
            self.mod_lattice[working_scope_name].update_expr((ident_name,ident_no), value_expr)
            
            # if this identifier is a class /function def 
            if isinstance(value_expr, DefIdentObject):
                self.mod_lattice[working_scope_name].update_value((ident_name,ident_no), value_expr)
                continue 
            elif isinstance(value_expr, ast.Lambda):
                self.mod_lattice[working_scope_name].update_value((ident_name,ident_no), DefIdentObject("lambda"))
                continue 
            elif isinstance(value_expr, TypeObject):
                self.mod_lattice[working_scope_name].update_value((ident_name,ident_no), value_expr)
                continue
                
            elif isinstance(value_expr, ExternalObject):   
                self.mod_lattice[working_scope_name].add_type_link(ident_name, ident_no, value_expr, scope_name = "external")
                self.mod_lattice[working_scope_name].update_value((ident_name,ident_no), value_expr)
                continue 
            
            #var_val = self.visit_expression(value_expr)
           # this is def only mode 
           
            if DEFONLY:
                #name_val_lookup = lambda x: None
                continue
            else:

                # access local def-use 
                name_val_lookup = lambda x: self.query_value(x,working_scope_name, self.mod_lattice)
                try: 
                    var_val = literal_eval(value_expr, name_val_lookup)
                except:
                    var_val = None 
            
                
            # by disabling this part
            if var_val is not None:
                self.mod_lattice[working_scope_name].update_value((ident_name,ident_no), var_val)
            else:
                # TODO: if not evaluated successfully, we will move to using the expression to tell the type 
                #self.mod_lattice[working_scope_name].update_value((ident_name,ident_no), value_expr )
                if type(value_expr) == ast.Call:
                    
                    func_name = get_func(value_expr)
                    name_parts = func_name.split(".")
                    func_name_head = name_parts[0]
                
                    if  hasattr(value_expr.func, "id"):
                        if is_class_name(func_name_head):
                            obj = TempObject(value_expr.func.id)  # return an empty object
                            self.mod_lattice[working_scope_name].update_value((ident_name,ident_no), obj)
 
                        elif func_name_head == "cls":
                            parent_scope = working_scope_name.split(".")[-2]
                            self.mod_lattice[working_scope_name].add_type_link(ident_name, ident_no, "<cls>", scope_name = parent_scope)
                    
                        else:
                            self.mod_lattice[working_scope_name].add_type_link(ident_name, ident_no, "<ret>", scope_name = value_expr.func.id)
                       
                        # note here, we all the member of the class rather than the ret

                    elif isinstance(value_expr.func, ast.Attribute):
                        # such as a.fun()
                        # such as super().func()  
                        # palse note that the overall node is func_call and the node.func is also a function call 
                        #print(working_scope_name, ident_name,  astor.to_source(value_expr).strip() )
                        #print(ast.dump(value_expr.value_expr.func.value))
                        '''
                        import classA
                        obj_a = ClassA()  # obj_a ::  ClassA
                        a = obj_a.attr #  get obj_a type first. 
                        '''
                        # value_expr is a call node
                        # value_expr.func = attr :
                        # attr := 
                        # func : =  Name | Attribute 
                        # attribute = value.attr 
                        func = value_expr.func   # 
                        # need to locate which scope is the first one 
                        attr_value = func.value 
                        attr_name = func.attr
                      
                        
                        if isinstance(attr_value, ast.Name):
                            # such as self.fun()
                            # object function call
                            #print("this is object function call")
                            # sg.reso
                            assigned_obj = self.restore_obj_acess(attr_value.id, working_scope_name, self.mod_lattice)
                            if assigned_obj:
                                if isinstance(assigned_obj, DefIdentObject):
                                    cls_name = assigned_obj.name
                                    func_name = cls_name +"." + attr_name
                                    self.mod_lattice[working_scope_name].add_type_link(ident_name, ident_no, "<ret>",  scope_name=func_name)
                                elif isinstance(assigned_obj, TempObject):
                                    cls_name = assigned_obj.cls_name
                                    func_name = cls_name +"." + attr_name
                                    self.mod_lattice[working_scope_name].add_type_link(ident_name, ident_no, "<ret>",  scope_name=func_name)
                                elif isinstance(assigned_obj, ExternalObject):
                                    #print("testing")
                                    pass 

                        elif isinstance(attr_value, ast.Call):
                            # call chain    
                            # such as super().fun()
                            #print("this is function call chain")
                            if hasattr(attr_value.func, "id"):
                                call_header = attr_value.func.id 
                                if call_header == "super":
                                    cur_cls_name = parent_scope_name.split(".")[-1]
                                    #print(ast.dump(attr_value), cur_cls_name, attr_name)
                                    cls_name = self.sg.MRO_resolve_method(cur_cls_name, attr_name)
                                    if cls_name:
                                        func_name = cls_name+"."+attr_name
                                        self.mod_lattice[working_scope_name].add_type_link(ident_name, ident_no, "<ret>",  scope_name=func_name)

                elif type(value_expr) == ast.Attribute:
                    attr_name = value_expr.attr
                    if hasattr(value_expr.value, "id"):
                        #TODO: to test what value has no id in the value clause in the given value expression?
                        first_part = value_expr.value.id
                        attr_name = value_expr.attr
                       
                        if first_part == "self":
                            constructor_scope_name = f"{parent_scope_name}.__init__"
                            self.mod_lattice[working_scope_name].add_type_link(ident_name, ident_no, first_part+"."+attr_name, scope_name=constructor_scope_name)
                    # elif first_part == "super"
                        else:
                            res = self.sg.name_lookup(first_part, working_scope_name)
                    elif type(value_expr.value) == ast.Call:
                        # disable this part to do scope anaysis
                        func_node = value_expr.value.func 
                        if hasattr(func_node, "id") and func_node.id == "super":
                            cur_cls_name = parent_scope_name.split(".")[-1]
                            
                            cls_name = self.sg.MRO_resolve_method(cur_cls_name, attr_name)
                            if cls_name:
                                self.mod_lattice[working_scope_name].add_type_link(ident_name, ident_no, attr_name, scope_name=cls_name)

    
            # need to locate 
       
    def get_values(self, scope_name):
        self.mod_lattice[scope_name].print_values()
        
    def get_types(self, scope_name):
        self.mod_lattice[scope_name].get_types()

    def get_type_links(self, scope_name):
        return self.mod_lattice[scope_name].get_type_links()
    
    def get_call_types(self, stmt):
        visitor = CallTypeHints()
        visitor.visit(stmt)
        return visitor.type_hints

    def drive(self, GEN_STUB=False):
        """
        Infer the types for the modules accessible from the entrypoint
        """
        # Loop through leaves

        for node in self.leaves:
            if node.ast is None:
                node.node_type_links = {}
                node.mod_lattice = {} 
                continue
            user_type_info = None 
            if ENFORCE_USER_TYPE:
                user_type_info = read_stub_types(node.ast)
        
            external_type_links, mod_lattice, scope_arg = self.run(node.ast, node.sg, mod_name=node.full_name)
            
            node.node_type_links =  external_type_links
            node.mod_lattice = mod_lattice 
            node.scope_arg = scope_arg
            node.user_type_info = user_type_info
            
        if not DEFONLY and not DEFUSEONLY:
            self.run_import_anaysis()
        
    
        for node in self.leaves:
            if node.ast is not None and  len(node.mod_lattice)>0:
                node_type_dict = self.harvest_all_types(node.ast, node.mod_lattice, user_type_info=node.user_type_info)
                node.node_type_dict = node_type_dict
                node_type_gt = self.harvest_all_annotations(node.ast)
                node.node_type_gt =  node_type_gt
    
    def run(self, ast_tree, sg, mod_name = ""):
      
        self.mod_lattice = {}   
        self.external_type_links = {}
        mod_cfg = CFGBuilder().build("mod", ast_tree)
        self.sg = sg
        

        def process_cfg(scope_cfg, scope_name = [], scope_type = "mod", arg_dict = {}):

            scope_name_str = ".".join(scope_name)
            parent_scope_name = ".".join(scope_name[:-1])
            self.mod_lattice[scope_name_str] = CCPLattice()
            self.scope_args[scope_name_str] = arg_dict
            ssa_analyzer = SSA()
            ssa_results, ident_const_dict, id2blocks = ssa_analyzer.compute_SSA(scope_cfg)

            for var_name, expr in arg_dict.items():
                # it does not make any sense to infer types for self
                if var_name!="self":
                    #ident_const_dict[("<arg>."+var_name, 0)] = expr
                    ident_const_dict[(var_name, -1)] = expr
        
            
            if scope_type == "cls":
                self.mod_lattice[scope_name_str].add_var(("self", 0))
                self.mod_lattice[scope_name_str].update_value(("self", 0), TempObject(scope_name[-1]))

                self.mod_lattice[scope_name_str].add_var(("cls", 0))
                self.mod_lattice[scope_name_str].update_value(("cls", 0), TempObject(scope_name[-1]))
            
                self.mod_lattice[scope_name_str].add_var(("<cls>", 0))
                self.mod_lattice[scope_name_str].update_value(("<cls>", 0), TempObject(scope_name[-1]))
                csn = scope_name_str + ".__init__"
            
            self.type_infer(ident_const_dict, scope_name_str, parent_scope_name= parent_scope_name, is_inside_class = True)
            
            for b_id, ssa_reps in ssa_results.items():
                for idx, stmt_rep in enumerate(ssa_reps):
                    if "isinstance" not in stmt_rep:
                        continue 
                    stmt = id2blocks[b_id].statements[idx]

                    if DEFONLY or DEFUSEONLY: # do not name resolution 
                        continue 
                    type_hints = self.get_call_types(stmt)
                    for var_name, type_name in type_hints.items():
                        if var_name in arg_dict:
                            self.mod_lattice[scope_name_str].update_type((var_name,0), type_name)
                            
            
            for fun_name_tup, fun_cfg in scope_cfg.functioncfgs.items():
                fun_name = fun_name_tup[1]
                arg_dict = scope_cfg.function_args[fun_name_tup]
                process_cfg(fun_cfg, scope_name = scope_name + [fun_name], scope_type = "func", arg_dict=arg_dict)
            
            for cls_name, cls_cfg in scope_cfg.class_cfgs.items():
                process_cfg(cls_cfg, scope_name = scope_name +[cls_name], scope_type = "cls")
                pass 

        
        process_cfg(mod_cfg, scope_name = ["<mod>"])  

        if DEFONLY or DEFUSEONLY:
            # no name resolution accessed
            return self.external_type_links, self.mod_lattice, self.scope_args
        
         # to process the body
        
        for scope_name, var_lattice in self.mod_lattice.items():
            type_links =  var_lattice.get_type_links()
           
            for (ident_name, no), (target, target_scope_name) in type_links.items(): 
               
                if target_scope_name is None:    
                    continue
            
                final_target_scope_name = self.lookup_scope_name(scope_name, target_scope_name, self.mod_lattice) 
         
               
                if final_target_scope_name:
                    #print(self.mod_lattice[final_target_scope_name].print_values())
                    target_value = self.mod_lattice[final_target_scope_name].get_value_by_name(target)    
                    target_expr = self.mod_lattice[final_target_scope_name].get_expr(target)
                    
                    var_lattice.update_value((ident_name, no), target_value)
                    var_lattice.update_expr((ident_name, no), target_expr)
                else:
                    scope_obj = self.query_value(target_scope_name, "mod", self.mod_lattice)
                    if scope_obj and isinstance(scope_obj, ExternalObject):
                        # here the key is still ident name, no but the value for the val here should be <ret> and target scope name in the given node 
                        # target scope is soemthign like mod+"target_scope_name"
                        self.external_type_links[(ident_name, no, scope_name)] = (scope_obj, target)
                     
                        pass 
        
        return self.external_type_links, self.mod_lattice, self.scope_args



    def annotation2str(self, annotation):
        """
        clean the source of annotations 
        """
        if annotation is None:
            return None 
        annot_src = astor.to_source(annotation).strip()
        annot_src = re.sub('\n|"',  '',    annot_src)
        return annot_src

    def eval_results(self, output_dir):
        import json 
        n_arg_types = 0
        n_arg_total = 0
        n_ret_total = 0
        n_ret_types = 0
        n_local = 0
        output_data = []
        
        for node in self.leaves:
            if len(node.mod_lattice)==0:
                continue 
            for fun_name, fun_type_gt in node.node_type_gt.items():    
                if "<mod>."+fun_name not in node.node_type_dict:
                     continue    
                fun_type_pred = node.node_type_dict["<mod>."+fun_name]
                args = node.scope_arg["<mod>."+fun_name]
                for var_name, annot in fun_type_gt.items():
                    if var_name not in fun_type_pred:
                        print("not found")
                        continue 
                    pred_type = fun_type_pred[var_name]
                    # this is to count precison 
                    if annot is None:
                        continue 
                    annot_src = self.annotation2str(annot)
                    if pred_type in invalid_type_annotations or annot_src in invalid_type_annotations:
                        continue 
                    # this is to count precison 
                    if var_name not in fun_type_pred:
                        continue         
                    exec_rec = {
                        "ep":self.entry_point,
                        "fn":node.prefix,
                        "fun_name":fun_name,
                        "var_name":var_name,
                        "pred": pred_type,
                        "annot_src":annot_src
                    }
                    if var_name == "<ret>":
                        exec_rec["loc"] = "<ret>"
                    elif var_name in args:
                        #exec_rec = f"Debugging: {self.entry_point},{fun_name}, <arg>, {var_name}, {pred_type}, {annot_src}"
                        exec_rec["loc"] = "<arg>"
                    else:
                        exec_rec["loc"] = "<local>"
                    output_data.append(exec_rec)
        

        filename = self.entry_point.replace("/", "-").lstrip(".-")  + ".json"
        dest = os.path.join(output_dir, filename)
        f = open(dest, 'w')
        json_content = json.dumps(output_data)     
        f.write(json_content)
        f.close() 
      
    
    
    def dump(self, debug=False):
        inferred_results = {}
        for node in self.leaves:
#            n_total += len(node.node_type_dict)
            #print(node.prefix, )
            
            if len(node.mod_lattice)==0:
                continue
            inferred_results["name"] = node.prefix
            inferred_results["pred"] = node.node_type_dict
            node_type_gt = node.node_type_gt


            inferred_results["gt"] = node_type_gt #ode.node_type_gt
        #print("testing")
        for k, v in inferred_results["pred"].items():
            print(k, v)
    
    def to_json(self, output_dir):
        # line by line 
        import json 
        
        output_data = {
            "entry_point":self.entry_point,
            "type_data": []  # a list of types  # from scope to 
        }
        for node in self.leaves:
            if len(node.mod_lattice)==0:
                continue
       
            for fun_name, fun_type_dict in node.node_type_dict.items():  
                #print(node.prefix, fun_name)
                scope_type_data = {
                    "mod_name":node.prefix, 
                    "scope_name": fun_name,
                    "<local>":{},
                    "<arg>":{}, 
                    "<ret>":{}
                }
                for var_name, annot in fun_type_dict.items():
                    if annot is None or annot  in invalid_type_annotations:
                       if var_name == "<ret>":
                            continue 
            #        #print(var_name, annot)
                    if var_name == "<ret>":
                         scope_type_data["<ret>"] = annot 
                    elif var_name in node.scope_arg[fun_name]:
                         scope_type_data["<arg>"][var_name] = annot
                    else:
                        scope_type_data["<local>"][var_name] = annot
                output_data["type_data"].append(scope_type_data)

        print(output_data)
        filename = self.entry_point.replace("/", "-").lstrip(".-")  + ".json"
       

        #f = open(output_dir+'/'+filename, 'w')
        #json_content = json.dumps(output_data)     
        #f.write(json_content)
        #f.close() 
       
    def harvest_all_annotations(self, ast_tree, mode="src"):
        type_dict = read_stub_types(ast_tree)
        return type_dict
     

    
    def harvest_all_types(self, ast_tree, mod_lattice, user_type_info=None):
        mod_type_info = {}
        if ast_tree is None:
            return mod_type_info
        #for scope_name, scope_lattice in mod_lattice.items():
        #    type_info = scope_lattice.get_types()
        #    if user_type_info is not None and scope_name in user_type_info:
        #        scope_user_type_info = user_type_info[fun_name]
        #        for ident_name, type_annot in fun_user_type_info.items():
        #            if type_annot is None:
        #                continue 
        #            type_annot_src = self.annotation2str(type_annot)
        #            type_info[ident_name] = type_annot_src
    
        #        pass 
        #    mod_type_info[scope_name] = type_info
       #      type_info = scope_lattice.get_types()
            # use type correction 
        #    if  user_type_info is not None and fun_name in user_type_info:
        #        pass 
        #    pass 
        
        for stmt in ast_tree.body:
            if type(stmt) == ast.FunctionDef:
                shallow_scope_name = "<mod>."+ stmt.name
                fun_name = stmt.name 
                type_info = mod_lattice[shallow_scope_name].get_types()
                #ret_type_annot = get_user_annotate(stmt)
                #user_type_info = read_from_func_def(stmt)
                if  user_type_info is not None and fun_name in user_type_info:
                    fun_user_type_info = user_type_info[fun_name]
                    for ident_name, type_annot in fun_user_type_info.items():
        #                #print(type_annot, 'testing', type(type_annot))
                        if type_annot is None:
                            continue 
                        type_annot_src = self.annotation2str(type_annot)
                        type_info[ident_name] = type_annot_src
    
                mod_type_info[shallow_scope_name] = type_info
                
            elif type(stmt) == ast.ClassDef:
                for c_stmt in stmt.body:
                    if type(c_stmt) == ast.FunctionDef:
                        fun_name = stmt.name + "." + c_stmt.name
                        shallow_scope_name = "<mod>."+ fun_name
                        if shallow_scope_name not in mod_lattice:
                            continue 
                        else:
                            type_info = mod_lattice[shallow_scope_name].get_types()
                            if  user_type_info is not None and fun_name in user_type_info:
                                fun_user_type_info = user_type_info[fun_name]
                                for ident_name, type_annot in fun_user_type_info.items():
                                    #print(type_annot, 'testing', type(type_annot))
                                    if type_annot is None:
                                        continue 
                                    type_annot_src = self.annotation2str(type_annot)
                                    type_info[ident_name] = type_annot_src
                    
                            #print(type_info)
                            mod_type_info[shallow_scope_name] = type_info
    
        return mod_type_info
                      
    def run_import_anaysis(self):

        for node in self.leaves:
            for ident, target in node.node_type_links.items():      
                ident_name, ident_no, original_scope_name = ident[0],ident[1], ident[2]
                target_scope = target[0]
                target_name = target[1]
                imported_path = target_scope.imported_path
                imported_name = target_scope.imported_name
                if imported_path is None:
                    continue 

                target_node = self.import_graph.go_to_that_node(node, imported_path.split("."))
                if target_node is None:
                    continue 
                #print(ident, target)
                if not hasattr(target_node, "mod_lattice"):
                    #TODO: to debug the case 
                    continue
                new_val = self.query_value(target_name, "mod."+imported_name, target_node.mod_lattice)
                if new_val is None:
                    continue 
                node.mod_lattice[original_scope_name].update_value((ident_name, ident_no), new_val)
                #TODO: need a class to model all the data in one value 
                # it's a class object, providing interface for all queries of different purpose 
    
    def scan_user_type(self, GEN_STUB=False):
        """
        Infer the types for the modules accessible from the entrypoint
        """
        n_ret = 0
        n_arg = 0
        n_local = 0
        for node in self.leaves:
            if node.ast is None:
                node.node_type_links = {}
                node.mod_lattice = {} 
                continue
                user_type_info = read_stub_types(node.ast)
                
   
    def drive(self, GEN_STUB=False):
        """
        Infer the types for the modules accessible from the entrypoint
        """
        # Loop through leaves

        for node in self.leaves:
            if node.ast is None:
                node.node_type_links = {}
                node.mod_lattice = {} 
                continue
            user_type_info = None 
            if ENFORCE_USER_TYPE:
                user_type_info = read_stub_types(node.ast)
        
            external_type_links, mod_lattice, scope_arg = self.run(node.ast, node.sg, mod_name=node.full_name)
            
            node.node_type_links =  external_type_links
            node.mod_lattice = mod_lattice 
            node.scope_arg = scope_arg
            node.user_type_info = user_type_info
            
        if not DEFONLY:
            self.run_import_anaysis()
    
        for node in self.leaves:
            if node.ast is not None and  len(node.mod_lattice)>0:
                node_type_dict = self.harvest_all_types(node.ast, node.mod_lattice, user_type_info=node.user_type_info)
                node.node_type_dict = node_type_dict
                node_type_gt = self.harvest_all_annotations(node.ast)
                node.node_type_gt =  node_type_gt


def ablation(entry_point):
    #output_dir = "exp-Feb/ablation/top50-def"
    #output_dir = "exp-Feb/ablation/top50-use"
    #output_dir = "exp-Feb/ablation/top50-full"
    #output_dir = "exp-Feb/ablation/large-def"
    #output_dir = "exp-Feb/ablation/large-use"
    #output_dir = "exp-Feb/ablation/large-full"

    #output_dir = "exp-Feb/ablation/top50-pure-static"
    #output_dir = "exp-Feb/ablation/large-pure-static"
    
    #output_dir = "exp-Feb/ablation/top50-no-user"
    #output_dir = "exp-Feb/ablation/large-no-user"
    
    output_dir = "debugging"
    
    
    inferrer = TypeInference(entry_point)
    inferrer.drive()
    inferrer.to_json(output_dir)
    return 0
 
    
    
    pass  
def processing_sinle(entry_point):
    
    # evaluate 
    #output_dir = "exp-Feb/eval_res/top50"
    #output_dir = "exp-Feb/num_res/large"
    #output_dir = "exp-Feb/eval_2-2/top50"
    #output_dir = "exp-Feb/eval_2-2/large"
  
    
    
    #output_dir = "exp-Feb/num_res/large"
    #output_dir = "exp-Feb/num_res/top50"
        
    inferrer = TypeInference(entry_point)
    inferrer.drive()
    inferrer.eval_results(output_dir)

    return 0
 
        
    
    #inferrer.dump()
    #out_str = ""
    #return out_str 

def main():
    entry_point = sys.argv[1]
    ablation( entry_point)
    #out_str = processing_sinle(entry_point)
 
# TODO: next, 

if __name__ == "__main__":
    main()
