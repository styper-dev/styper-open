# from (HiTyper Project)[https://github.com/JohnnyPeng18/HiTyper/blob/main/hityper/typeobject.py]
import re

builintypes = {}
builintypes["element"] = ["bool", "int", "float", "None", "Any", "Text", "type", "bytes"]
builintypes["generic"] = [ "List", "Tuple", "Set", "Dict", "Union", "Optional", "Callable", "Iterable", "Sequence", "Generator"]
builintypes["rare"] = ["complex", "bytearray", "Frozenset", "memoryview", "range"]

invalid_type_annotations = [None, "any", "Any", "call",  "_", "None", "typing.Any", "NoReturn", "_T0", "_T1", "_T", "_FuncT", "Optional"]

simplified_types = {
    #builtins
    "dict_keys": "set",
    "dict_values": "set",
    "dict_items": "set",
    "typing.NoReturn": "None",
    "typing.AnyStr": "str",
    "typing.ByteString": "str",
    "typing.TypedDict": "Dict",
    "typing.FrozenSet": "frozenset",
    "typing.DeafultDict": "Dict",
    "typing.OrderedDict": "Dict",
    "typing.ItemsView": "Set",
    "typing.KeysView": "Set",
    "typing.Mapping": "Dict",
    "typing.MappingView": "Dict",
    "typing.MutableMapping": "Dict",
    "typing.MutableSequence": "List",
    "typing.MutableSet": "Set",
    "typing.Sequence": "List",
    "typing.ValuesView": "List",
    "typing.AbstractSet": "Set",
    "typing.Text": "str",
    #collections module
    "collections.ChainMap": "Dict",
    "collections.Counter": "Dict",
    "collections.OrderedDict": "Dict",
    "collections.defaultdict": "Dict",
    "collections.UserDict": "Dict",
    "collections.UserList": "List",
    "collections.UserString": "str",
    "collections.abc.Iterable": "List",
    "collections.abc.Generator": "Generator",
    "collections.abc.Callable": "Callable",
    "collections.abc.MutableSequence": "List",
    "collections.abc.ByteString": "str",
    "collections.abc.Set": "Set",
    "collections.abc.MutableSet": "Set",
    "collections.abc.Mapping": "Dict",
    "collections.abc.MutableMapping": "Dict",
    "collections.abc.MappingView": "Dict",
    "collections.abc.ItemsView": "Set",
    "collections.abc.KeysView": "Set",
    "collections.abc.ValuesView": "Set",
    "collections.abc.AsyncIterable": "List",
    "collections.abc.AsyncGenerator": "Generator"
}


def match_types(pred, gt):
    
    if pred == gt:
        return True

    # our tool uses lower case to represent
    if gt in ["List", "Tuple", "Set", "Dict"]:
        gt = gt.lower()
        return match_types(pred, gt)
        
    if gt in simplified_types:
        return match_types(pred, simplified_types[gt])
    if pred in simplified_types:
        return match_types(simplified_types[pred], gt)

    gt = re.sub('(typing|t|\_t)\.|"',  '',    gt)
    pred = re.sub('(typing|t|\_t)\.|"',  '',    pred)
    if gt.find("builtins.")>0:
        gt = gt[9:]
   
    gt_old = gt 
    
    idx  = gt.find("[")
    if idx>0:
        gt = gt[0:idx]
        
    if pred == "self":
        return True 
    elif pred==gt:
        return True 
    

    def match(pattern, pred):
        for value in pred:
            if pattern in value:
                return True
        return False
    
    if gt is None and pred is None:
        return True
    
    if gt[-1]  ==  pred:
        return True
    if gt.lower() == pred or pred.lower() == gt:
        return True 
    if gt in ["object", "Any"]:
        return True 
        return True
    # generators are indeed
    # https://docs.python.org/3/library/typing.html 
    # this is what the documentation says  annotate your generator as having a return type of either Iterable[YieldType] or Iterator[YieldType]:
    elif gt in ["Generator", "Iterable", "Iterator"] and pred == "generator":
        return True 
    elif gt == "Sequence" and pred in ["list", "bytes"]:
        return True
    elif gt == "Dict" and pred == "dict":
        return True 
    elif gt == "Mapping" and pred in ["CallbackDict", "dict", "Dict"]:
        return True
    # this is the offical type alias  
    elif gt in ["typing.Text", "Text", "AnyStr"] and pred == "str":
        return True 
    elif gt == "BinaryIO" and pred in ["io.BytesIO", "BytesIO"]:
        return True
    elif gt == "Iterable" and pred  in ["list", "set"]:
        return True 
    elif gt  == "Optional" and gt_old.find(pred)>=0:
        return True 
    elif gt == "Union" and gt_old.find(pred)>=0:
        return True 
    
    return False
