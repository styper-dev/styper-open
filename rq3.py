import enum
import ast 
import re 
import os
from re import L
import sys
import csv 
import json
from unittest import result
import astor 
from read_stub import read_stub_types
from match import match_types

invalid_type_annotations = [None, "any", "Any", "_", "None", "typing.Any", "NoReturn", "_T0", "_T1", "_T", "_FuncT"]

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
    scope_data = {}
     # scope_name,  var_name, var_type, typeannot 
    for fn, res in hittyper_data.items():
       
        #print(partial_name, all_subject_files[0])
       
        # file list applied 
        if fn not in allowed_fn and len(allowed_fn)>0:
            continue 

        for k, v in res.items():
            
            scope_names = k.split("@")
            first_part = scope_names[0]
            second_part = scope_names[1]
            
            if second_part == "global" and first_part == "global":
                scope_name = "<mod>"
            elif second_part == "global":
                # see the case 
                scope_name = "<mod>" + "." + first_part
                pass 
            else:
                scope_name = "<mod>" + "." + second_part + "."+first_part
            #print(fn, scope_name)
            new_func_name = scope_names[1] + "." + scope_names[0]

                        
            new_func_type = {   "<ret>":{},
                                "<local>": {},
                                "<arg>": {}
                            }
            for ele in v:
                #print(ele)        
                if is_valid_type(ele["type"]):
                    out_str = f"{fn}, {scope_name},{ele['category']}, {ele['name']}, {ele['type'][0]}"
                    print(out_str)
                   
                
                    
    #print(f",{n_arg}, {n_return}，{n_local}")


    return 0

def count_hityper_batch():
    #all_fns = os.listdir("hityper-output-top50")
    #data_dir = "hityper-output-top50-1.12"
    #data_dir = "hityper-output-top50"
    
    data_dir = "hityper/hityper-output-large-1.18/"
    
    dataset_fns = open("hityper_files.txt").read().splitlines()
    dataset_fns = [ "/data/someone/hiper-data/dataset/"+fn for fn in dataset_fns ]
    all_fns = os.listdir(data_dir)
    for fn in all_fns:
        if fn.endswith("json"):
            res = count_hityper_lib(os.path.join(data_dir, fn), allowed_fn=())
            #print(res)
            pass 

    

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

        fn = "/data/someone/hiper-data/dataset/"+fn.strip()
        
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
             
                if v is None:

                    continue 
                if hasattr(v, "id") and v.id == "Any":
                    continue
                if type(v) == ast.Constant and v.value == None:
                    continue

                
                type_src = astor.to_source(v).strip()
                type_src = re.sub(r'(\n+| +)', '', type_src)
             
                   
                
                if type_src in invalid_type_annotations:
                    continue 
                scope_name ='<mod>.'+fun_name
              
                if var_name == "<ret>":
                    out_str = f"{fn},{scope_name},return, {var_name}, {type_src}"
                  
                else:
                    out_str = f"{fn},{scope_name},arg, {var_name}, {type_src}"
                   
                print(out_str)
                


def count_pytype_lib():
 
    #base_dir = "pytype-lib-10-res/pyi/"

    all_lib_eps = open("exp/top50.eps").readlines()
    
    for idx, entry_point in enumerate(all_lib_eps):
        #print(idx, entry_point)
        entry_point = entry_point.strip()
        # this is for pytype
        dest = os.path.join("pytype-lib-50-jan-26/", str(idx+1), "pyi")
        
        # this is for pyre 
        #dest = os.path.join(entry_point,".pyre/types")

        pyi_files = get_path_by_ext(dest)
        #print(dest)
        

    
        for pyi_file in pyi_files:
            
            pyi_fn_parts = pyi_file.split("/")
            # for pytype
            rel_path = "/".join(pyi_fn_parts[3:])


            # for pyre 
            #rel_path = "/".join(pyi_fn_parts[8:])
           
            

            #print(entry_point, rel_path)
            ref_fn = entry_point + "/"+ rel_path
            ref_fn = ref_fn[:-1]


         
            src = open(pyi_file).read()
            # reference filename 

            #print(pyi_file)
      
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
                    type_src = re.sub(r'(\n+| +)', '', type_src)
             
                    if type_src in invalid_type_annotations:
                        continue 
                    #print(type_src)
                    #print(ast.dump(v))
                    scope_name ='<mod>.'+fun_name
                    if var_name == "<ret>":
                        out_str = f"{ref_fn},{scope_name},return,{var_name},{type_src}"
                  
                    else:
                        out_str = f"{ref_fn},{scope_name},arg,{var_name}, {type_src}"
                    print(out_str)

        pass 


            



def count_pyre_new():

    all_fns = open("all.hityper.files").readlines()
    n = 0
    n_correct = 0    
    
    base_dir = "/data/someone/STyper_exp/hityer_files/"

    #base_dir = ""
    
    n_ret = 0
    n_arg  = 0
    for idx, fn in enumerate(all_fns):
        dest = os.path.join(base_dir, str(idx), ".pyre", "types")
        fn = "/data/someone/hiper-data/dataset/"+fn.strip()
        #print(dest)
        #print(dest)
        
        pyi_files = get_path_by_ext(dest)
        #print(pyi_files)
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
                type_src = re.sub(r'(\n+| +)', '', type_src)
             
                
                if type_src in invalid_type_annotations:
                    continue 
                #print(type_src)
                #print(ast.dump(v))

                scope_name ='<mod>.'+fun_name
                if var_name == "<ret>":
                    out_str = f"{fn},{scope_name},return,{var_name},{type_src}"
                  
                else:
                    out_str = f"{fn},{scope_name},arg,{var_name}, {type_src}"
                print(out_str)

def count_styper():
    base_dir = "RQ2/styper-output-large-json/"

    base_dir = "exp-Feb/num_res/large/"

    base_dir = "exp-Feb/ablation/top50-full/"
    base_dir = "exp-Feb/ablation/large-full/"
    
    
    all_json_outputs = os.listdir(base_dir)
    all_project_outputs = [json.loads(open(base_dir + fn).read()) for fn in all_json_outputs] 
    #print(len(all_project_outputs))
  
    #out_str = f"{fn},{scope_name},return,{var_name},{type_src}"

    n_ret = 0
    n_local = 0
    n_arg = 0
    for output in all_project_outputs:
        ep = output["entry_point"]
        for scope_type_info in output["type_data"]:
            #print(scope_type_info.keys())
            #fn = ep + scope_type_info["mod_name"]
            #print(fn)
            if "<ret>" in scope_type_info and scope_type_info["<ret>"] and scope_type_info["<ret>"]!="Optional":
                out_str = f"{ep},{scope_type_info['scope_name']},return,ret, {scope_type_info['<ret>']}"
                print(out_str)
                n_ret += 1

            for var_name, type_src in scope_type_info["<arg>"].items():
                if type_src and type_src!="Optional":
                    type_src = re.sub(r'(\n+| +)', '', type_src)
                    out_str = f"{ep},{scope_type_info['scope_name']},arg, {var_name}, {type_src}"
                    print(out_str)
                    


            for var_name, type_src in scope_type_info["<local>"].items():
                if type_src and type_src!="Optional":
                    type_src = re.sub(r'(\n+| +)', '', type_src)
                    out_str = f"{ep},{scope_type_info['scope_name']},local, {var_name}, {type_src}"
                    print(out_str)
    

def count_styper_lib():
    #base_dir = "RQ2/styper-output-json/"
    #base_dir = "exp-Feb/num_res/top50/"
    base_dir = "exp-Feb/ablation/top50-full/"
    base_dir = "exp-Feb/ablation/large-full/"
    
    
    all_json_outputs = os.listdir(base_dir)
    all_project_outputs = [json.loads(open(base_dir + fn).read()) for fn in all_json_outputs] 
    #print(len(all_project_outputs))
  
    #out_str = f"{fn},{scope_name},return,{var_name},{type_src}"
    for output in all_project_outputs:
        ep = output["entry_point"]
        ep_parts = ep.split("/")
       
        
        for scope_type_info in output["type_data"]:
            #print(scope_type_info.keys())
            filename = scope_type_info["mod_name"]
            filename = filename.replace(".", "/") + ".py"
            #print(ep, filename)
            
            filename = "/".join(ep_parts[:-1]) +"/" +filename
            #print(filename)
           
            if "<ret>" in scope_type_info and scope_type_info["<ret>"] and scope_type_info["<ret>"] not in invalid_type_annotations:
                out_str = f"{filename},{scope_type_info['scope_name']},return,ret, {scope_type_info['<ret>']}"
                print(out_str)

            for var_name, type_src in scope_type_info["<arg>"].items():
                if type_src not in invalid_type_annotations:
                    type_src = re.sub(r'(\n+| +)', '', type_src)
                    out_str = f"{filename},{scope_type_info['scope_name']},arg, {var_name}, {type_src}"
                    print(out_str)


            for var_name, type_src in scope_type_info["<local>"].items():
                if type_src not in invalid_type_annotations:
                    type_src = re.sub(r'(\n+| +)', '', type_src)
                    out_str = f"{filename},{scope_type_info['scope_name']},local, {var_name}, {type_src}"
                    print(out_str)



def venn():


    def load_csv(fn):

        type_annots = {}
        all_lines = open(fn).read().splitlines()
        n_dup = 0
        
        for line in all_lines:
            row = line.split(",")
            filename = row[0].strip()
            scope_name = row[1].strip()
            var_type = row[2].strip()
            var_name = row[3].strip()
            if len(row)>5:
                #print(type_src, row[4:])
                type_src = ",".join(row[4:]).lstrip().rstrip()
            else:
                type_src = row[4].lstrip().rstrip()
                #all_records.add(key)
            key = (filename, scope_name, var_type,var_name)
            if key in type_annots:
                "duplicate due to override class"
                n_dup += 1
            else:
                type_annots[(filename, scope_name, var_type,var_name)] = type_src

        #print(len(type_annots), 'key')
        return type_annots, len(all_lines) 
        


# load dataset


    
    hityper_large_rec, N_large  = load_csv("RQ3/hityper_output_large_csv.csv")
    hityper_lib_rec, N_top = load_csv("RQ3/hityper_output_top50_csv.csv")

    print(f"HiTyper: {N_large} & {N_top}")
  
    hityper_large_rec.update(hityper_lib_rec)
    n_hityper = N_large+N_top
    
    pytype_large_rec, N_large = load_csv("RQ3/pytype-output-large_csv.csv")
    pytype_lib_rec,N_top  = load_csv("RQ3/pytype-output-top50_csv.csv")
    print(f"pytype: {N_large} & {N_top}")

    n_pytype = N_large+N_top
  
    pytype_large_rec.update(pytype_lib_rec)

    pyre_large_rec, N_large = load_csv("RQ3/pyre-output-large_csv.csv")
    pyre_lib_rec, N_top = load_csv("RQ3/pyre-output-top50_csv.csv")
    n_pyre = N_large+N_top
  
    print(f"pyre: {N_large} & {N_top}")
    pyre_large_rec.update(pyre_lib_rec)
  
    
    styper_large_rec, N_large = load_csv("RQ3/large.styper.lines")
    styper_lib_rec, N_top = load_csv("RQ3/top50.styper.lines")
    n_styper = N_large+N_top

    print(f"styper: {N_large} & {N_top}")

    styper_large_rec.update(styper_lib_rec)

    styper_keys = set(styper_large_rec.keys())
    hityper_keys = set(hityper_large_rec.keys())
    pytype_keys = set(pytype_large_rec.keys())
    pyre_keys = set(pyre_large_rec.keys())

    
    print("Styper vs Hityper:", n_styper,  len(styper_keys.intersection(hityper_keys)), n_hityper)
    print("Styper vs pytype:", n_styper,  len(styper_keys.intersection(pytype_keys)), n_pytype)
    print("Styper vs pyre:", n_styper,  len(styper_keys.intersection(pyre_keys)), n_pyre)
   
    styper_hityper_keys = styper_keys.intersection(hityper_keys)
    styper_pytype_keys = styper_keys.intersection(pytype_keys)
    styper_pyre_keys = styper_keys.intersection(pyre_keys)


    common_N = len(styper_hityper_keys)
    n = 0
    for k in styper_hityper_keys:
        styper_type = styper_large_rec[k]
        hityper_type = hityper_large_rec[k]
        if match_types(styper_type, hityper_type):
            n += 1
        else:  
            pass  
            #print(styper_type, hityper_type)
    print(n, common_N, n/common_N)

    
    
    common_N = len(styper_pytype_keys)
    n = 0
    for k in styper_pytype_keys:
        styper_type = styper_large_rec[k]
        pt_type = pytype_large_rec[k]
        if match_types(styper_type, pt_type):
            n += 1
        else:    
            #print(styper_type, '|||||||||||', pt_type)
            pass 
    print(n, common_N, n/common_N)

    common_N = len(styper_pyre_keys)
    n = 0
    for k in styper_pyre_keys:
        styper_type = styper_large_rec[k]
        pyre_type = pyre_large_rec[k]
        if match_types(styper_type, pyre_type):
            n += 1
        else:  
            pass  
            #print(styper_type, pyre_type)
    print(n, common_N, n/common_N)
    
    

        
if __name__ == "__main__":
    #count_pytype_single_lib()
    #count_pytype_lib()
    
    #count_pytype_new()
    #count_pytype_lib()
    
    #count_pyre_new()
    
    #count_styper()
    #count_styper_lib()

    venn()
    
    #count_csv(sys.argv[1])
    #count_hityper_batch()

    
