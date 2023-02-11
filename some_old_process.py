import enum
import ast 
import os
from re import L
import sys
import json
from unittest import result
import astor 
from read_stub import read_stub_types


def count_hityper(filename):
    
    raw_hityper_data = open(filename).read()
    hittyper_data = json.loads(raw_hityper_data)
    tmp_data = hittyper_data.keys()
    all_fun_names = []
    all_fun_and_types = {}
    n_returns = 0
    n_local = 0
    n_arg = 0
    for type_type, all_data in hittyper_data.items():
   
        for fn, tmp_data in all_data.items():
            #for k, v in tmp_data.items():
            #print(k,v )
            print(fn)
            for scope_name, scope_data in tmp_data.items():
            
                for k_, v_ in scope_data.items():
                    #print(k_, v_["annotations"])
                    
                    annots = v_["annotations"]
                    #print(v_.keys())
                    #continue 
                    #print(k_, annots)
                    for ant in annots:
                        fun_name_tmp = fn +"."+scope_name +"."+ant["name"]

                        if ant["category"] == "return":
                            #print(k_, k, ant["type"])
                            n_returns  += 1
                            #if ant["type"]=="None":
                            #    continue 
                            #print(fun_name_tmp)
                            #all_fun_names.append(fn+"."+scope_name+"."+ant["name"])
                            #if ant["name"] == " ":
                            
                            if fun_name_tmp in all_fun_and_types:
                                print("duplicate")

                                all_fun_and_types[fun_name_tmp].append(ant["type"])
                            else:
                                all_fun_and_types[fun_name_tmp] = [ant["type"]]

                        elif ant["category"] == "local":
                           # print(ant["type"])
                            n_local += 1
                        else:
                            n_arg += 1
                            
                            #pall_fun_names.append(fn)
    #keys = list(hittyper_data.keys())
    #print(keys)
    #print(n_returns)
    #all_fun_names = set(all_fun_names)
    #print(len(all_fun_names))
    #print(len(all_fun_and_types))
    print(n_returns, n_arg, n_local )
  
def count_hityper_lib(json_file, allowed_fn = set()):

    # to count how many of types are valid  and compare the number with our approach see coverage 
    # to count how many types are matched with our appraoch
    
  
    type_dict = {"<ret>":{},
                "<local>": {},
                "<arg>": {}
    }
    def is_valid_type(type_lst):
        if len(type_lst) == 0:
            return False 
        if len(type_lst) == 1 and type_lst[0] == 'None':
            return False 
        #print(type_lst)
        return True


    raw_hityper_data = open(json_file).read()
    hittyper_data = json.loads(raw_hityper_data)
    n_return = 0
    n_arg = 0
    n_local = 0

    for fn, res in hittyper_data.items():
       
        #print(partial_name, all_subject_files[0])
        if fn not in allowed_fn:
            continue 

        for k, v in res.items():
            scope_names = k.split("@")
            new_func_name = scope_names[1] + "." + scope_names[0] 
            new_func_type = {   "<ret>":{},
                                "<local>": {},
                                "<arg>": {}
                            }
            for ele in v:
                #print(ele)        
                if ele["category"] == "return" and is_valid_type(ele["type"]):
                    #print("testing", ele["name"], ele["type"])
                    #new_func_type["<return>"] = ele["type"]
                    n_return += 1
                elif ele["category"] == "local" and is_valid_type(ele["type"]):
                    n_local += 1
                    #print(ele["category"], ele["name"], ele["type"])
                elif ele["category"] == "arg" and is_valid_type(ele["type"]):
                    n_arg += 1
    print(f"{n_return},{n_arg},{n_local}")
    #print(f"Return {n_return}, Arg: {n_arg}, Local: {n_local}")

    return 0

def count_hityper_batch():
    #all_fns = os.listdir("hityper-output-top50")
    data_dir = "hityper-output-top50-1.12"
    data_dir = "hityper-output-top50"
    data_dir = "hityper/hityper-output-large-1.18/"
    dataset_fns = open("hityper_files.txt").read().splitlines()
    dataset_fns = [ "/data/someone/hiper-data/dataset/"+fn for fn in dataset_fns ]
    all_fns = os.listdir(data_dir)
    for fn in all_fns:
        if fn.endswith("json"):
            res = count_hityper_lib(os.path.join(data_dir, fn), allowed_fn=dataset_fns)
            #print(res)
            pass 

    
def get_fns():

    #filename = "/data/someone/hiper-data/dataset/ManyTypes4Py_gts_test_verified.json" 
    filename = "/data/someone/hiper-data/dataset/ManyTypes4Py_gts_test_verified_detailed.json" 
    
    #gt_file = "/data/someone/hiper-data/dataset/ManyTypes4Py_gts_test_verified.json"
    #gt_data = json.loads(open(gt_file).read())
    raw_hityper_data = open(filename).read()
    hittyper_data = json.loads(raw_hityper_data)
    all_files = []

    for type_type, all_data in hittyper_data.items():
        for fn, tmp_data in all_data.items():
            all_files.append(fn)

    #print(len(all_files))   
    all_repos = []
    
    all_files = list(set(all_files))


    for fn in all_files:
        print(fn)
        
        #repo_name = "/".join(fn.split("/")[0:2])
        #all_repos.append(repo_name)
    
    #print(len(all_repos))
    #all_repos = list(set(all_repos))
    #for repo_name in all_repos:
    #    print(repo_name)
    #return 0




def verify():

    #filename = "/data/someone/hiper-data/dataset/ManyTypes4Py_gts_test_verified.json" 
    filename = "/data/someone/hiper-data/dataset/ManyTypes4Py_gts_test_verified_detailed.json" 
    gt_file = "/data/someone/hiper-data/dataset/ManyTypes4Py_gts_test_verified.json"
    gt_data = json.loads(open(gt_file).read())
    raw_hityper_data = open(filename).read()
    hittyper_data = json.loads(raw_hityper_data)

    for k, v in gt_data.items():
        pass 
    n_returns = 0
    #print(len(hittyper_data.keys()))
    #print(hittyper_data["repos/zhbei/Sublime-Text-3/Backup/20171106085312/mdpopups/st3/mdpopups/version.py"])
    #return 0
#    tmp_data = hittyper_data["generic"]["repos/gacou54/pyorthanc/pyorthanc/patient.py"]
    all_fun_names = []
    all_fun_and_types = {}
    for type_type, all_data in hittyper_data.items():
        for fn, tmp_data in all_data.items():
            #for k, v in tmp_data.items():
            #print(k,v )
            for scope_name, scope_data in tmp_data.items():
                #print(scope_name)
                if scope_name != "TestSamenessValidationChecker":
                #if scope_name != "ConductorCompiler":
                    continue

                for k_, v_ in scope_data.items():
                    #print(k_, v_["annotations"])
                    annots = v_["annotations"]
                    #print(v_.keys())
                    #continue 
                    #print(k_, annots)
                    for ant in annots:
                        if ant["category"] == "return":
                            #print(k_, k, ant["type"])
                            n_returns  += 1
                            #if ant["type"]=="None":
                            #    continue 
                            fun_name_tmp = fn +"."+scope_name +"."+ant["name"]
                            #print(fun_name_tmp)
                            #all_fun_names.append(fn+"."+scope_name+"."+ant["name"])
                            #if ant["name"] == " ":
                            print(ant)
                            print(fn)
                            if fun_name_tmp in all_fun_and_types:
                                all_fun_and_types[fun_name_tmp].append(ant["type"])
                            else:
                                all_fun_and_types[fun_name_tmp] = [ant["type"]]

                            #pall_fun_names.append(fn)
    #keys = list(hittyper_data.keys())
    #print(keys)
    #print(n_returns)
    #all_fun_names = set(all_fun_names)
    print(len(all_fun_names))
    print(len(all_fun_and_types))
    #return 0
    for k, v in all_fun_and_types.items():
        #print(k)
        v = set(v)
        if "None" in v and len(v) == 1:
            #print("testing", v )
            pass 
        #else:
        #    print(k)
    #for fun_name in all_fun_names:
    #    print(fun_name)
    return 0


    #keys = keys
    for fn in keys:
        #print(k)
        #continue
        #
        if fn != "repos/gacou54/pyorthanc/pyorthanc/patient.py":
            continue 
        type_dict = hittyper_data[fn]
        #print(type_dict)
        for k, v in type_dict.items():
            scope_names = k.split("@")
            #new_func_name = scope_names[1] + "." + scope_names[0] 
            #new_func_type = {   "<ret>":{},
            #                    "<local>": {},
            #                    "<arg>": {}
            #           
            #print(fn, k, v.keys())
            print(v["get_identifier"])
            for scope_name, results in v.items():
                #print(results)
                print(scope_name)
                for name, res  in results.items():
                    #print(scope_name, res)
                    for ele in res:
                        #print(type(ele))
                        #print(ele)
                        if isinstance(ele, list):
                            continue 
                        if ele["category"] == "return" and ele["type"] != "None":
                            n_returns += 1
                            print(name, ele["name"] , ele["type"])
                   #for ele in v:
                #print(ele)        

            #    if ele["category"] == "return":  # and is_valid_type(ele["type"]):
                    #print("testing", ele["name"], ele["type"])
                    #new_func_type["<return>"] = ele["type"]
            #        n_return += 1
         
                pass

            continue      
            #for ele in v:
                #print(ele)        

            #    if ele["category"] == "return":  # and is_valid_type(ele["type"]):
                    #print("testing", ele["name"], ele["type"])
                    #new_func_type["<return>"] = ele["type"]
            #        n_return += 1
                    
            #    elif ele["category"] == "local" : #and is_valid_type(ele["type"]):
            #        n_local += 1
                        
                    #print(ele["category"], ele["name"], ele["type"])
            #    elif ele["category"] == "arg" :# and is_valid_type(ele["type"]):
            #        n_arg += 1
    
        pass 
    print(n_returns)
    return 0
    for key, val in hittyper_data.items():
        print(key)
     #   break 
    
def main():

    # to count how many of types are valid  and compare the number with our approach see coverage 
    # to count how many types are matched with our appraoch
    
    all_folders = open("top-10.folder").read().splitlines()
    type_dict = {"<ret>":{},
                "<local>": {},
                "<arg>": {}
    }
    def is_valid_type(type_lst):
        if len(type_lst) == 0:
            return False 
        if len(type_lst) == 1 and type_lst[0] == 'None':
            return False 
        return True

    json_file = sys.argv[1]

    raw_hityper_data = open(json_file).read()
    hittyper_data = json.loads(raw_hityper_data)
    n_return = 0
    n_arg = 0
    n_local = 0

    for fn, res in hittyper_data.items():
        partial_name = fn[32:]
        if partial_name not in all_subject_files:
            continue 
        #print(partial_name, all_subject_files[0])
        for k, v in res.items():
            scope_names = k.split("@")
            new_func_name = scope_names[1] + "." + scope_names[0] 
            new_func_type = {   "<ret>":{},
                                "<local>": {},
                                "<arg>": {}
                            }
            for ele in v:
                #print(ele)        
                if ele["category"] == "return" and is_valid_type(ele["type"]):
                    #print("testing", ele["name"], ele["type"])
                    #new_func_type["<return>"] = ele["type"]
                    n_return += 1
                elif ele["category"] == "local" and is_valid_type(ele["type"]):
                    n_local += 1
                    #print(ele["category"], ele["name"], ele["type"])
                elif ele["category"] == "arg" and is_valid_type(ele["type"]):
                    n_arg += 1
    print(f"{n_return},{n_arg},{n_local}")
    #print(f"Return {n_return}, Arg: {n_arg}, Local: {n_local}")

    return 0

def process_pytype(self, lib_name):
    from read_stub import read_stub_types
        
    base_dir = f"./pytype-res/pyi/{lib_name}"

    #base_dir = f"top-10/.pyre/types/{lib_name}/tmp/{lib_name}"
    #print(base_dir)
    ##base_dir = "./typeshed/stubs/Jinja2"
    #base_dir = "./typeshed/stubs/Flask"
    
    n_fun_all = 0
    n_tmp = 0
    #n_all, n_modules = lookup_typeshed(base_dir, ep)
    for leaf_node in self.leaves:
        leaf_path_segments = leaf_node.prefix.split(".")
        
        pyi_file_path = os.path.join(base_dir,"/".join(leaf_path_segments[1:]) + ".pyi") 
        
        if os.path.exists(pyi_file_path):
            
            shed_type_dict = read_stub_types(open(pyi_file_path).read())
            #n_fun_typed += n_returns
            for k, v in shed_type_dict.items():
                if v is None:
                    continue 
                if hasattr(v, "id") and v.id == "Any":
                    continue
                if type(v) == ast.Constant and v.value == None:
                    continue

                if hasattr(v, "id") and v.id == "str":
                    n_tmp += 1

                n_fun_all += 1
        print(n_fun_all)

  

def count_pytype():
    
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
    pass 

def count_pyre():
    all_fns = open("all.hityper.files").readlines()
    n = 0
    n_correct = 0

    for fn in all_fns:
        fn = fn.strip()
        parts = fn.split("/")

        repo_dir = "/data/someone/hiper-data/dataset/" + "/".join(parts[0:2])
        rel_path = "/".join(parts[2:]) + "i"
        pyi_file = repo_dir + "/.pyre/types/" + rel_path

        if os.path.exists(pyi_file):
            #print("testing")
            n_correct += 1
            pass 
        else:
            pass 
            print("failed")
        
    print(n_correct)


def seperate_files():
    import shutil


    all_fns = open("all.hityper.files").readlines()
    
    n = 0
    n_correct = 0

    base_dir = "/data/someone/STyper_exp/hityer_files"
    original_dir = "/data/someone/hiper-data/dataset"
    
    for idx, fn in enumerate(all_fns):
        fn = fn.strip()
        parts = fn.split("/")
        dest_folder = os.path.join(base_dir, str(idx))
        os.makedirs(dest_folder)
        src_path  = os.path.join(original_dir, fn)
        shutil.copy(src_path,dest_folder)


# scan a folder recurisively and return all files ending with the flag
def get_path_by_ext(root_dir, flag='.pyi'):
    paths = []
    for root, dirs, files in os.walk(root_dir):
    #    files = [f for f in files if not f[0] == '.']  # skip hidden files such as git files
        #dirs[:] = [d for d in dirs if not d[0] == '.']
        for f in files:
            if f.endswith(flag):
                paths.append(os.path.join(root, f))
    return paths

def count_ptype_single_lib():
    
    dest = os.path.join(base_dir, str(idx), "pyi")
    pyi_files = get_path_by_ext(dest)
    pass 



def count_pytype_new():
    all_fns = open("all.hityper.files").readlines()
    
    n = 0
    n_correct = 0

    base_dir = "/data/someone/STyper_exp/pytype_output"
    n_ret = 0
    n_arg  = 0
    for idx, fn in enumerate(all_fns):
        dest = os.path.join(base_dir, str(idx), "pyi")
        pyi_files = get_path_by_ext(dest)
        if len(pyi_files) == 0:
            continue 
        pyi_file = pyi_files[0]
        src = open(pyi_file).read()
        try: 
            ast_tree = ast.parse(src)
        except:
            ast_tree = None 
        
        if ast_tree is None:
            continue 

        stub_type_dict = read_stub_types(ast_tree)
        #n_fun_typed += n_returns
        
        for fun_name, type_res in stub_type_dict.items():
            for var_name, v in type_res.items():
                #print(type_src)

            
                if v is None:

                    continue 
                if hasattr(v, "id") and v.id == "Any":
                    continue
                if type(v) == ast.Constant and v.value == None:
                    continue

                
                type_src = astor.to_source(v).strip()
                
                if type_src in [None, "None", "typing.Any", "NoReturn", "_T0", "_T1", "_T", "_FuncT"]:
                    continue 
                if type_src == "_":
                    continue 
                #print(type_src)
                #print(ast.dump(v))

                if var_name == "<ret>":
                    n_ret += 1
                else:
                    n_arg += 1

                #if hasattr(v, "id") and v.id == "str":
                #    n_tmp += 1

        #print(dest)
    print(n_ret, n_arg)


def count_pytype_lib():
 
    #base_dir = "pytype-lib-10-res/pyi/"

    base_dir = "pytype-lib-50-res=new/"
    

    #names = ["flask",  "jinja2",  "markupsafe", "_pytest" ,   "pytz",  "requests",  "six", "werkzeug"]
    names = ['tmp']
    #pyi_files = get_path_by_ext("./pytype-lib-50-res-new/pyi/")
    #pyi_files = get_path_by_ext("/data/someone/top-50-eps-pyre/.pyre/types/")

    #print(len(pyi_files))
    for name in names:
        n_ret = 0
        n_arg  = 0
        #dest = os.path.join("/data/someone/top-50-eps-pyre/.pyre/types/")
        dest = "/data/someone/top-50-eps/.pyre/types/"
        #dest = "pytype-lib-50-res-new-tmp/pyi/"
        pyi_files = get_path_by_ext(dest)
        print(len(pyi_files), '---')
        for pyi_file in pyi_files:
            
            src = open(pyi_file).read()
      
            #ast_tree = ast.parse(src)
            try: 
                ast_tree = ast.parse(src)
            except:
                ast_tree = None 
                pass 
            
            if ast_tree is None:
                continue 

            stub_type_dict = read_stub_types(ast_tree)
                        #n_fun_typed += n_returns
            
            for fun_name, type_res in stub_type_dict.items():
                for var_name, v in type_res.items():
                    #print(type_src)                
                    if v is None:
                        continue 
                    if hasattr(v, "id") and v.id == "Any":
                        continue
                    if type(v) == ast.Constant and v.value == None:
                        continue
                    type_src = astor.to_source(v).strip()
                    if type_src in [None, "None", "typing.Any", "NoReturn", "_T0", "_T1", "_T", "_FuncT", "object"]:
                        continue 
                    if type_src == "_":
                        continue 
                    #print(type_src)
                    #print(ast.dump(v))
                    if var_name == "self":
                        continue  
                    
                    if var_name == "<ret>":
                        n_ret += 1
                    else:
                        ##print(var_name, type_src)
                        n_arg += 1

                    #if hasattr(v, "id") and v.id == "str":
                #    n_tmp += 1

        #print(dest)
    
        print(name, n_ret, n_arg)



def count_pyre_lib_batch():


    #eps = open("exp/top_50_eps.txt").read().splitlines()

    eps = open("exp/top50.eps").read().splitlines()

    for ep in eps:
        n_ret = 0
        n_arg  = 0
        dest = os.path.join(ep, ".pyre", "types")
        print(dest)
        pyi_files = get_path_by_ext(dest)
        #print(len(pyi_files),'---')
        for pyi_file in pyi_files:
            src = open(pyi_file).read()
            try: 
                ast_tree = ast.parse(src)
            except:
                ast_tree = None 
            
            if ast_tree is None:
                continue 

            stub_type_dict = read_stub_types(ast_tree)
            #n_fun_typed += n_returns
            
            for fun_name, type_res in stub_type_dict.items():
                for var_name, v in type_res.items():
                    #print(type_src)

                
                    if v is None:

                        continue 
                    if hasattr(v, "id") and v.id == "Any":
                        continue
                    if type(v) == ast.Constant and v.value == None:
                        continue

                    
                    type_src = astor.to_source(v).strip()
                    
                    if type_src in [None, "None", "typing.Any", "NoReturn", "_T0", "_T1", "_T", "_FuncT"]:
                        continue 
                    if type_src == "_":
                        continue 
                    #print(type_src)
                    #print(ast.dump(v))

                    if var_name == "<ret>":
                        n_ret += 1
                    else:
                        n_arg += 1

                    #if hasattr(v, "id") and v.id == "str":
                    #    n_tmp += 1

        #print(dest)
        print(n_ret,",", n_arg)

            


def count_pyre_new():

    all_fns = open("all.hityper.files").readlines()
    n = 0
    n_correct = 0
    
    #base_dir = "/data/someone/STyper_exp/hityer_files/"
    
    base_dir = ""
    n_ret = 0
    n_arg  = 0
    for idx, fn in enumerate(all_fns):
        dest = os.path.join(base_dir, str(idx), ".pyre", "types")

        #print(dest)
        
        pyi_files = get_path_by_ext(dest)
        if len(pyi_files) == 0:
           # print("testing")
            continue 
        pyi_file = pyi_files[0]
        src = open(pyi_file).read()
        try: 
            ast_tree = ast.parse(src)
        except:
            ast_tree = None 
        
        if ast_tree is None:
            continue 

        stub_type_dict = read_stub_types(ast_tree)
        #n_fun_typed += n_returns
        
        for fun_name, type_res in stub_type_dict.items():
            for var_name, v in type_res.items():
                #print(type_src)
                if v is None:
                    continue 
                if hasattr(v, "id") and v.id == "Any":
                    continue
                if type(v) == ast.Constant and v.value == None:
                    continue
                type_src = astor.to_source(v).strip()
                
                if type_src in [None, "None", "typing.Any", "NoReturn", "_T0", "_T1", "_T", "_FuncT"]:
                    continue 
                if type_src == "_":
                    continue 
                #print(type_src)
                #print(ast.dump(v))

                if var_name == "<ret>":
                    n_ret += 1
                else:
                    n_arg += 1

                #if hasattr(v, "id") and v.id == "str":
                #    n_tmp += 1

        #print(dest)
    print(n_ret, n_arg)


def count_source_files():
    
    dest = "/data/someone/top-50-eps/"
    all_files = get_path_by_ext(dest, flag=".py")
    print(len(all_files))


if __name__ == "__main__":
    #count_pytype_single_lib()
    #count_pytype_lib()
    #count_pytype_new()
    #count_pytype_lib()
    #count_pyre_lib_batch()
    # ../dl-evaluation/dl-type-eval/top-10-new/
    #count_pyre_new()
    #seperate_files()
    #get_fns()
    #main()
    #count_ptype()
    #count_pyre()
    #count_hityper()
    #count_hityper_batch()
    #verify()
    #debug()
   # count_source_files()
