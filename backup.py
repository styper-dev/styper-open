def process_pytype(self, lib_name):
        from read_stub import read_stub_types
            
        base_dir = f"./pytype-res/pyi/{lib_name}"
        base_dir = f"top-10/.pyre/types/{lib_name}/tmp/{lib_name}"
        #print(base_dir)
        ##base_dir = "./typeshed/stubs/Jinja2"
        #base_dir = "./typeshed/stubs/Flask"
       
        n_fun_all = 0
        n_tmp = 0
        #n_all, n_modules = lookup_typeshed(base_dir, ep)
        pytype_type_res = {}
        for leaf_node in self.leaves:
            leaf_path_segments = leaf_node.prefix.split(".")        
            pyi_file_path = os.path.join(base_dir,"/".join(leaf_path_segments[1:]) + ".pyi") 
            if os.path.exists(pyi_file_path):
                shed_type_dict = read_stub_types(open(pyi_file_path).read())
                pytype_type_res[leaf_node.prefix] = shed_type_dict
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

