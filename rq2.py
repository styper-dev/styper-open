import os
import json 
import sys 

def count_styper(base_dir):
    
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
            if "<ret>" in scope_type_info and scope_type_info["<ret>"] and scope_type_info["<ret>"]!="Optional" :
                #out_str = f"{ep},{scope_type_info['scope_name']},return,ret, {scope_type_info['<ret>']}"
                #print(out_str)
                n_ret += 1

            for var_name, type_src in scope_type_info["<arg>"].items():
                if type_src and type_src!="Optional":
                    #type_src = re.sub(r'(\n+| +)', '', type_src)
                    #out_str = f"{ep},{scope_type_info['scope_name']},arg, {var_name}, {type_src}"
                    n_arg += 1

            for var_name, type_src in scope_type_info["<local>"].items():
                if type_src and type_src!="Optional":
                    n_local += 1
                    #print(type_src)
                    #type_src = re.sub(r'(\n+| +)', '', type_src)
                    #out_str = f"{ep},{scope_type_info['scope_name']},local, {var_name}, {type_src}"
    n_all = n_ret + n_local+ n_arg
    out_str = f"{n_arg:,} & {n_ret:,} & {n_local:,} & {n_all:,}"
    print(out_str)

def main():
    base_dir = sys.argv[1]
    #base_dir = "RQ3/top50-base/"
    #base_dir = "RQ3/top50-def-use/"
    #base_dir = "RQ3/top50-full/"
    
    
    count_styper(base_dir)
    pass 

if __name__ == "__main__":
    main()
