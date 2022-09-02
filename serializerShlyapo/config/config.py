
from types import FunctionType, CodeType, LambdaType
import inspect
import builtins

primitives = (int, str, bool, float)

def serialize_object(obj):

    if isinstance(obj, primitives):
        return obj
    elif is_function(obj):
        return serialize_function(obj)
    elif inspect.iscode(obj):
        return deserialize_inner_func(obj)
    elif inspect.isclass(obj):
        return serialize_class(obj)
    elif is_iterable(obj):
        return serialize_iterable(obj)
    else:
        return pack_object(obj)


def deserialize_object(src):
    if isinstance(src, primitives):
        return src
    elif isinstance(src, dict):
        if "function" in src.values():
            return deserialize_function(src)
        elif "object" in src.values():
            return unpack_object(src)
        elif "class" in src.values():
            return deserialize_class(src)
        else:
            return deserialize_iterable(src)
    elif is_iterable(src):
        return deserialize_iterable(src)


def is_iterable(obj):
    return getattr(obj, "__iter__", None) is not None


def is_function(obj):
    return inspect.isfunction(obj) or inspect.ismethod(obj) or isinstance(obj, LambdaType)


def serialize_function(obj):
    result = {"__type__": "function"}
    if inspect.ismethod(obj):
        obj = obj.__func__
    result["__name__"] = obj.__name__
    globs = get_global_vars(obj)
    result["__globals__"] = serialize_iterable(globs)
    arguments = {}
    for (key, value) in inspect.getmembers(obj.__code__):
        if key.startswith("co_"):
            if isinstance(value, bytes):
                value = list(value)
            if is_iterable(value) and not isinstance(value, str):
                converted_vals = []
                for val in value:
                    if val is not None:
                        converted_vals.append(serialize_object(val))
                    else:
                        converted_vals.append("!None")
                arguments[key] = converted_vals
                continue
            arguments[key] = value
    result["__args__"] = arguments
    return result


def deserialize_function(src):
    arguments = src["__args__"]
    globs = src["__globals__"]
    globs["__builtins__"] = builtins
    for key in src["__globals__"]:
        if key in arguments["co_names"]:
            globs[key] = deserialize_object(src["__globals__"][key])

    temp_consts = []
    for val in list(arguments["co_consts"]):
        func = deserialize_object(val)
        if is_function(func):
            val = deserialize_object(val)
            temp_consts.append(val.__code__)
            continue
        temp_consts.append(val)
    arguments["co_consts"] = temp_consts

    for val in arguments:
        if is_iterable(arguments[val]) and not isinstance(arguments[val], str):
            temp_ls = []
            for value in arguments[val]:
                if value == "!None":
                    temp_ls.append(None)
                else:
                    temp_ls.append(value)
            arguments[val] = temp_ls

    coded = CodeType(arguments['co_argcount'],
                     arguments['co_posonlyargcount'],
                     arguments['co_kwonlyargcount'],
                     arguments['co_nlocals'],
                     arguments['co_stacksize'],
                     arguments['co_flags'],
                     bytes(arguments['co_code']),
                     tuple(arguments['co_consts']),
                     tuple(arguments['co_names']),
                     tuple(arguments['co_varnames']),
                     arguments['co_filename'],
                     arguments['co_name'],
                     arguments['co_firstlineno'],
                     bytes(arguments['co_lnotab']),
                     tuple(arguments['co_freevars']),
                     tuple(arguments['co_cellvars']))
    return FunctionType(coded, globs)


def serialize_class(obj):
    result = {'__type__': 'class', '__name__': obj.__name__}
    for attr in dir(obj):
        if attr == "__init__":
            attr_value = getattr(obj, attr)
            result[attr] = serialize_function(attr_value)
        if not attr.startswith('__'):
            attr_value = getattr(obj, attr)
            result[attr] = serialize_object(attr_value)
    return result


def deserialize_class(src):
    ex = {}
    for attr, value in src.items():
        ex[attr] = deserialize_object(value)
    return type(src["__name__"], (), ex)


def get_global_vars(func):
    globs = {}
    for global_var in func.__code__.co_names:
        if global_var in func.__globals__:
            globs[global_var] = func.__globals__[global_var]
    return globs


def serialize_iterable(obj):
    if isinstance(obj, list) or isinstance(obj, tuple):
        packed_iterable = []
        for value in obj:
            if value is None:
                packed_iterable.append("!None")
            packed_iterable.append(serialize_object(value))
        return packed_iterable
    elif isinstance(obj, dict):
        packed_dict = {}
        for key, value in obj.items():
            packed_dict[key] = serialize_object(value)
        return packed_dict


def deserialize_iterable(obj):
    if isinstance(obj, list) or isinstance(obj, tuple):
        unpacked_iterable = []
        for value in obj:
            if value == "!None":
                unpacked_iterable.append(None)
            unpacked_iterable.append(deserialize_object(value))
        return unpacked_iterable
    elif isinstance(obj, dict):
        unpacked_dict = {}
        for key, value in obj.items():
            unpacked_dict[key] = deserialize_object(value)
        return unpacked_dict


def deserialize_inner_func(obj):
    return serialize_function(FunctionType(obj, {}))


def pack_object(obj):
    result = {"__type__": "object", "__class__": obj.__class__.__name__}
    for value in dir(obj):
        if not value.startswith("__"):
            value = serialize_object(getattr(obj, value))
            result[value] = value
    return result


def unpack_object(src):
    meta = type(src.get("__class__"), (), {})
    result = meta()
    for key, value in src.items():
        if key == '__class__':
            continue
        setattr(result, key, deserialize_object(value))
    return result
