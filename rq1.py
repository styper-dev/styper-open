import os
import sys
import re
import json

from match import match_types


def count_precision(all_lines):
    
    n_ret = 0
    n_ret_correct = 0
    n_arg = 0
    n_arg_correct = 0
    for line in all_lines:
        line = line.replace("\n", "")
        parts = line.strip().split(",")
        parts = map(lambda x:x.strip(), parts)
        parts = list(parts)
        if len(parts)<2:
            continue 
        if "Ret" ==line[0:3]:   
            n_arg_correct += int(parts[2])
            n_arg += int(parts[3])
            n_ret_correct += int(parts[4])
            n_ret += int(parts[5])
    return n_arg_correct, n_arg, n_ret_correct, n_ret 


def make_row(n_arg_correct, n_arg, n_ret_correct, n_ret):
    out_str = f"{n_arg_correct:,}/{n_arg:,}({n_arg_correct/n_arg:.3f})& {n_ret_correct:}/ {n_ret:,}({n_ret_correct/n_ret:.3f})"
    n_correct = n_arg_correct + n_ret_correct
    n_total = n_arg+n_ret
    total_str = f"{n_correct:,}/{n_total:,}({n_correct/n_total:.3f})"
    print(out_str+"& "+total_str)


def parse_every_line(all_lines):
    n_arg = 0
    n_arg_correct = 0
    n_ret = 0 
    n_ret_correct = 0

    for line in all_lines:
        var_name = line["var_name"]
        var_cate = line["loc"]
        pred = line["pred"]
        gt = line["annot_src"]
        if var_cate == "<arg>":
            n_arg += 1
           
            if match_types(pred, gt):
                n_arg_correct +=1
            else:
                out_str = f"debugging: {line['ep'].strip()},{line['fn']}.strip(), {line['fun_name']}, {var_name}, {pred}, {gt}"
                out_str = out_str.replace("\n", "")
                #print(out_str)
                
        if var_cate == "<ret>":
            n_ret += 1
            if match_types(pred, gt):
                n_ret_correct +=1
            else:
                #print(pred, gt)
                out_str = f"debugging: {line['ep']},{line['fn']}, {line['fun_name']}, {var_name}, {pred}, {gt}"
                out_str = out_str.replace("\n", "")
                #print(out_str)
                pass 
         
    n_all = n_arg+n_ret
    n_correct = n_arg_correct + n_ret_correct
    return n_arg_correct, n_arg, n_ret_correct,n_ret
    #print(f"{n_arg_correct:,}/{n_arg:,}({n_arg_correct/n_arg:.3f} ) & {n_ret_correct:,}/{n_ret:,}({n_ret_correct/n_ret:.3f}) & {n_correct:,}/{n_all:,}({n_correct/n_all:,.3f})")
def count_precision_all():
    
    top50_file = "RQ1/top50/"
    large_file = "RQ1/large/"

    n_arg_all = 0
    n_ret_all = 0
    n_arg_correct_all = 0
    n_ret_correct_all = 0


    top50_all_lines = process_json_files(top50_file)
    large_all_lines = process_json_files(large_file)
    
    PRINT_TABLE = True
    

    n_arg_correct, n_arg, n_ret_correct, n_ret  = parse_every_line(top50_all_lines)
    if PRINT_TABLE:
        make_row(n_arg_correct, n_arg, n_ret_correct, n_ret)
    
    n_arg_correct_all += n_arg_correct
    n_arg_all += n_arg

    n_ret_correct_all += n_ret_correct
    n_ret_all += n_ret
    
    n_arg_correct, n_arg, n_ret_correct, n_ret  = parse_every_line(large_all_lines)
    if PRINT_TABLE:
        make_row(n_arg_correct, n_arg, n_ret_correct, n_ret) 
    
    n_arg_correct_all += n_arg_correct
    n_arg_all += n_arg

    n_ret_correct_all += n_ret_correct
    n_ret_all += n_ret
    if PRINT_TABLE:
        make_row(n_arg_correct_all, n_arg_all, n_ret_correct_all, n_ret_all)
    
    
    #parse_every_line(large_all_lines)
    
    return 0 

def process_json_files(folder):
    all_fn_names = os.listdir(folder)
    all_lines = []
    for fn in all_fn_names:
        fn = os.path.join(folder, fn)
        content = open(fn).read()
        content = json.loads(content)
        all_lines += content
    return all_lines


if __name__ == "__main__":
    count_precision_all()
    
