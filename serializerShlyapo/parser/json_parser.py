
class Json:
    inspect = __import__('inspect')
    types = __import__('types')
    deque = getattr(__import__('collections'), 'deque')
    func_found = {}
    sort = False

    @staticmethod
    def dict_to_code(obj):
        return Json.types.CodeType(obj["co_argcount"],
                                   obj["co_posonlyargcount"],
                                   obj["co_kwonlyargcount"],
                                   obj["co_nlocals"],
                                   obj["co_stacksize"],
                                   obj["co_flags"],
                                   bytes(bytearray(Json.parse_array(obj["co_code"], 1)[0])),
                                   tuple(obj["co_consts"]),
                                   tuple(obj["co_names"]),
                                   tuple(obj["co_varnames"]),
                                   obj["co_filename"],
                                   obj["co_name"],
                                   obj["co_firstlineno"],
                                   bytes(bytearray(Json.parse_array(obj["co_lnotab"], 1)[0])),
                                   tuple(obj["co_freevars"]),
                                   tuple(obj["co_cellvars"]))

    @staticmethod
    def collect_funcs(obj, is_visited):
        for i in obj.__globals__:
            attr = obj.__globals__[i]
            if Json.inspect.isfunction(attr) and attr.__name__ not in is_visited:
                is_visited[attr.__name__] = attr
                is_visited = Json.collect_funcs(attr, is_visited)
        return is_visited

    @staticmethod
    def is_instance(obj):
        if not hasattr(obj, '__dict__'):
            return False
        if Json.inspect.isroutine(obj):
            return False
        if Json.inspect.isclass(obj):
            return False
        else:
            return True

    @staticmethod
    def dict_to_module(obj):
        try:
            return __import__(obj)
        except ModuleNotFoundError:
            raise ImportError(str(obj) + ' not found')

    @staticmethod
    def parse_dict(string, idx):
        args = {}
        comma = False
        colon = False
        phase = False
        temp = None
        try:
            next_char = string[idx]
        except IndexError:
            raise StopIteration(idx)

        while True:
            if next_char == '}':
                break
            elif next_char == ' ' or next_char == '\n':
                idx += 1
            elif next_char == ',':
                if comma is False:
                    raise StopIteration(idx)
                idx += 1
                phase = False
                comma = False
            elif next_char == ':':
                if colon is False:
                    raise StopIteration(idx)
                idx += 1
                phase = True
                colon = False
            elif not comma and not phase:
                if next_char == '"':
                    obj, idx = Json.parse_string(string, idx + 1)
                    if obj in args:
                        raise StopIteration(idx)
                    temp = obj
                    phase = False
                    colon = True
                else:
                    raise StopIteration(idx)
            elif not colon and phase:
                if next_char == '"':
                    obj, idx = Json.parse_string(string, idx + 1)
                    args[temp] = obj
                elif next_char.isdigit() or (next_char == '-' and string[idx + 1].isdigit()):
                    obj, idx = Json.parse_digit(string, idx)
                    args[temp] = obj
                elif next_char == '{':
                    obj, idx = Json.parse_dict(string, idx + 1)
                    args[temp] = obj
                elif next_char == '[':
                    obj, idx = Json.parse_array(string, idx + 1)
                    args[temp] = obj
                elif next_char == 'n' and string[idx:idx + 4] == 'null':
                    args[temp] = None
                    idx += 4
                elif next_char == 't' and string[idx:idx + 4] == 'true':
                    args[temp] = True
                    idx += 4
                elif next_char == 'f' and string[idx:idx + 5] == 'false':
                    args[temp] = False
                    idx += 5
                elif next_char == 'N' and string[idx:idx + 3] == 'NaN':
                    args[temp] = float('NaN')
                    idx += 3
                elif next_char == 'I' and string[idx:idx + 8] == 'Infinity':
                    args[temp] = float('Infinity')
                    idx += 8
                elif next_char == '-' and string[idx:idx + 9] == '-Infinity':
                    args[temp] = float('-Infinity')
                    idx += 9
                else:
                    raise StopIteration(string[idx])

                comma = True
            else:
                raise StopIteration(idx)

            try:
                next_char = string[idx]
            except IndexError:
                raise StopIteration(idx)

        if not comma and not colon and len(args) != 0:
            raise StopIteration(idx)
        if "##function_type##" in args and len(args.keys()) == 1:
            return Json.dict_to_func(args["##function_type##"]), idx + 1
        if "##static_method_type##" in args and len(args.keys()) == 1:
            return staticmethod(args["##static_method_type##"]), idx + 1
        if "##class_method_type##" in args and len(args.keys()) == 1:
            return classmethod(args["##static_method_type##"]), idx + 1
        if "##class_type##" in args and len(args.keys()) == 1:
            return Json.dict_to_class(args["##class_type##"]), idx + 1
        if "##instance_type##" in args and len(args.keys()) == 1:
            return Json.dict_to_obj(args["##instance_type##"]), idx + 1
        if "##module_type##" in args and len(args.keys()) == 1:
            return Json.dict_to_module(args["##module_type##"]), idx + 1
        if "##code_type##" in args and len(args.keys()) == 1:
            return Json.dict_to_code(args["##code_type##"]), idx + 1
        else:
            if Json.sort:
                return dict(sorted(args.items())), idx + 1
            else:
                return args, idx + 1

    @staticmethod
    def dict_to_class(cls):
        try:
            return type(cls["name"], tuple(cls["bases"]), cls["dict"])
        except IndexError:
            raise StopIteration("Incorrect class")

    @staticmethod
    def dict_to_obj(obj):
        try:
            def __init__():
                pass

            cls = obj["class"]
            temp = cls.__init__
            cls.__init__ = __init__
            res = obj["class"]()
            res.__dict__ = obj["vars"]
            res.__init__ = temp
            res.__class__.__init__ = temp
            return res
        except IndexError:
            raise StopIteration("Incorrect object")

    @staticmethod
    def set_funcs(obj, is_visited, gls):
        for i in obj.__globals__:
            attr = obj.__globals__[i]
            if Json.inspect.isfunction(attr) and attr.__name__ not in is_visited:
                is_visited[attr.__name__] = True
                attr.__globals__.update(gls)
                is_visited = Json.set_funcs(attr, is_visited, gls)
        return is_visited

    @staticmethod
    def dict_to_func(obj):
        res = Json.types.FunctionType(globals=obj["__globals__"],
                                      code=obj["__code__"],
                                      name=obj['__name__'])
        funcs = Json.collect_funcs(res, {})
        funcs.update({res.__name__: res})
        Json.set_funcs(res, {res.__name__: True}, funcs)
        res.__globals__.update(funcs)
        res.__globals__['__builtins__'] = __import__('builtins')
        return res

    @staticmethod
    def parse_digit(string, idx):
        first = idx
        try:
            while string[idx] == '.' or string[idx].isdigit() or string[idx] == 'e' or string[idx] == 'E' \
                    or string[idx] == '-' or string[idx] == '+':
                idx += 1
        except IndexError:
            pass

        res = string[first:idx]
        try:
            return int(res), idx
        except ValueError:
            try:
                return float(res), idx
            except ValueError:
                raise StopIteration(idx)

    @staticmethod
    def parse_string(string, idx):
        first = idx
        opened = False
        try:
            while string[idx] != '"' or opened:
                if string[idx] == '\\':
                    opened = not opened
                else:
                    opened = False
                idx += 1
        except IndexError:
            raise StopIteration(idx)
        return string[first:idx], idx + 1

    @staticmethod
    def parse_array(string, idx):
        args = Json.deque()
        comma = False

        try:
            next_char = string[idx]
        except IndexError:
            raise StopIteration(idx)

        while True:
            if next_char == ']':
                break
            elif next_char == ' ' or next_char == '\n':
                idx += 1
            elif next_char == ',':
                if comma is False:
                    raise StopIteration(idx)
                idx += 1
                comma = False
            elif not comma:
                if next_char == '"':
                    obj, idx = Json.parse_string(string, idx + 1)
                    args.append(obj)
                elif next_char.isdigit() or (next_char == '-' and string[idx + 1].isdigit()):
                    obj, idx = Json.parse_digit(string, idx)
                    args.append(obj)
                elif next_char == '{':
                    obj, idx = Json.parse_dict(string, idx + 1)
                    args.append(obj)
                elif next_char == '[':
                    obj, idx = Json.parse_array(string, idx + 1)
                    args.append(obj)
                elif next_char == 'n' and string[idx:idx + 4] == 'null':
                    args.append(None)
                    idx += 4
                elif next_char == 't' and string[idx:idx + 4] == 'true':
                    args.append(True)
                    idx += 4
                elif next_char == 'f' and string[idx:idx + 5] == 'false':
                    args.append(False)
                    idx += 5
                elif next_char == 'N' and string[idx:idx + 3] == 'NaN':
                    args.append(float('NaN'))
                    idx += 3
                elif next_char == 'I' and string[idx:idx + 8] == 'Infinity':
                    args.append(float('Infinity'))
                    idx += 8
                elif next_char == '-' and string[idx:idx + 9] == '-Infinity':
                    args.append(float('-Infinity'))
                    idx += 9
                else:
                    print(string[idx - 100:idx + 100])
                    raise StopIteration(idx)

                comma = True
            else:
                print(string[idx - 100:idx + 100])
                raise StopIteration(idx)

            try:
                next_char = string[idx]
            except IndexError:
                raise StopIteration(idx)
        if not comma and len(args) != 0:
            raise StopIteration(idx)
        return list(args), idx + 1

    @staticmethod
    def code_to_dict(obj):
        return {"##code_type##": {"co_argcount": obj.co_argcount,
                                  "co_posonlyargcount": obj.co_posonlyargcount,
                                  "co_kwonlyargcount": obj.co_kwonlyargcount,
                                  "co_nlocals": obj.co_nlocals,
                                  "co_stacksize": obj.co_stacksize,
                                  "co_flags": obj.co_flags,
                                  "co_code": obj.co_code,
                                  "co_consts": obj.co_consts,
                                  "co_names": obj.co_names,
                                  "co_varnames": obj.co_varnames,
                                  "co_filename": obj.co_filename,
                                  "co_name": obj.co_name,
                                  "co_firstlineno": obj.co_firstlineno,
                                  "co_lnotab": obj.co_lnotab,
                                  "co_freevars": obj.co_freevars,
                                  "co_cellvars": obj.co_cellvars
                                  }
                }

    @staticmethod
    def class_to_dict(cls):
        bases = ()
        if len(cls.__bases__) != 0:
            for i in cls.__bases__:
                if i.__name__ != "object":
                    bases += (Json.class_to_dict(i),)
        args = {}
        st_args = dict(cls.__dict__)
        if len(st_args) != 0:
            for i in st_args:
                if Json.inspect.isclass(st_args[i]):
                    args[i] = Json.class_to_dict(st_args[i])
                elif Json.inspect.isfunction(st_args[i]):
                    if st_args[i].__name__ not in Json.func_found:
                        args[i] = Json.function_to_dict(st_args[i])
                elif isinstance(st_args[i], staticmethod):
                    if st_args[i].__func__.__name__ not in Json.func_found:
                        args[i] = Json.static_method_to_dict(st_args[i])
                elif isinstance(st_args[i], classmethod):
                    if st_args[i].__func__.__name__ not in Json.func_found:
                        args[i] = Json.class_method_to_dict(st_args[i])
                elif Json.inspect.ismodule(st_args[i]):
                    args[i] = Json.module_to_dict(st_args[i])
                elif Json.is_instance(st_args[i]):
                    args[i] = Json.object_to_dict(st_args[i])
                elif isinstance(st_args[i],
                                (set, dict, list, int, float, type(True), type(False), type(None), tuple)):
                    args[i] = st_args[i]
        return {"##class_type##": {"name": cls.__name__, "bases": bases, "dict": args}}

    @staticmethod
    def object_to_dict(obj):
        return {"##instance_type##": {"class": Json.class_to_dict(obj.__class__), "vars": obj.__dict__}}

    @staticmethod
    def module_to_dict(obj):
        return {"##module_type##": obj.__name__}

    @staticmethod
    def collect_globals(obj, obj_code):
        Json.func_found[obj.__name__] = True
        gls = {}
        for i in obj_code.co_names:
            try:
                if Json.inspect.isclass(obj.__globals__[i]):
                    gls[i] = Json.class_to_dict(obj.__globals__[i])
                elif Json.inspect.isfunction(obj.__globals__[i]):
                    if obj.__globals__[i].__name__ not in Json.func_found:
                        gls[i] = Json.function_to_dict(obj.__globals__[i])
                elif isinstance(obj.__globals__[i], staticmethod):
                    if obj.__globals__[i].__func__.__name__ not in Json.func_found:
                        gls[i] = Json.static_method_to_dict(obj.__globals__[i])
                elif isinstance(obj.__globals__[i], classmethod):
                    if obj.__globals__[i].__func__.__name__ not in Json.func_found:
                        gls[i] = Json.class_method_to_dict(obj.__globals__[i])
                elif Json.inspect.ismodule(obj.__globals__[i]):
                    gls[i] = Json.module_to_dict(obj.__globals__[i])
                elif Json.is_instance(obj.__globals__[i]):
                    gls[i] = Json.object_to_dict(obj.__globals__[i])
                elif isinstance(obj.__globals__[i], (set, dict, list, int, float, bool, type(None), tuple, str)):
                    gls[i] = obj.__globals__[i]
            except KeyError:
                pass
        for i in obj_code.co_consts:
            if isinstance(i, Json.types.CodeType):
                gls.update(Json.collect_globals(obj, i))
        return gls

    @staticmethod
    def static_method_to_dict(obj):
        return {"##static_method_type##": Json.function_to_dict(obj.__func__)}

    @staticmethod
    def class_method_to_dict(obj):
        return {"##class_method_type##": Json.function_to_dict(obj.__func__)}

    @staticmethod
    def function_to_dict(obj):
        gls = Json.collect_globals(obj, obj.__code__)

        return {"##function_type##": {"__globals__": gls,
                                      "__name__": obj.__name__,
                                      "__code__":
                                          Json.code_to_dict(obj.__code__)
                                      }}

    @staticmethod
    def _dumps(obj, step='', new_step=''):
        if obj is None:
            return "null"
        elif obj is True:
            return "true"
        elif obj is False:
            return "false"
        elif obj is float("Inf"):
            return "Infinity"
        elif obj is float("-Inf"):
            return "-Infinity"
        elif obj is float("NaN"):
            return "NaN"
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, bytes):
            return "\"" + str(list(bytearray(obj))) + "\""
        elif isinstance(obj, str):
            return "\"" + obj.replace('\\', '\\\\').replace('\"', '\\\"') + "\""
        elif isinstance(obj, (set, tuple)):
            return Json.dumps_list(list(obj), step, new_step)
        elif isinstance(obj, list):
            return Json.dumps_list(obj, step, new_step)
        elif isinstance(obj, dict):
            return Json.dumps_dict(obj, step, new_step)
        elif Json.inspect.isfunction(obj):
            res = Json.dumps_dict(Json.function_to_dict(obj), step, new_step)
            Json.func_found = {}
            return res
        elif isinstance(obj, staticmethod):
            res = Json.dumps_dict(Json.static_method_to_dict(obj), step, new_step)
            Json.func_found = {}
            return res
        elif isinstance(obj, classmethod):
            res = Json.dumps_dict(Json.class_method_to_dict(obj), step, new_step)
            Json.func_found = {}
            return res
        elif Json.inspect.ismodule(obj):
            return Json.dumps_dict(Json.module_to_dict(obj), step, new_step)
        elif Json.inspect.isclass(obj):
            return Json.dumps_dict(Json.class_to_dict(obj), step, new_step)
        elif Json.is_instance(obj):
            return Json.dumps_dict(Json.object_to_dict(obj), step, new_step)
        elif isinstance(obj, Json.types.CodeType):
            return Json.dumps_dict(Json.code_to_dict(obj), step, new_step)
        else:
            raise TypeError()

    @staticmethod
    def dumps_list(obj, step="", new_step=""):
        if not len(obj):
            return "[]"
        new_step = "\n" + new_step
        res = "[" + new_step
        for i in range(len(obj) - 1):
            res += step + Json._dumps(obj[i], step, new_step.replace('\n', '') + step) + "," + new_step
        res += step + Json._dumps(obj[-1], step, new_step.replace('\n', '') + step) + new_step + "]"
        return res

    @staticmethod
    def dumps_dict(obj, step="", new_step=""):
        if not len(obj):
            return "{}"
        if Json.sort:
            obj = dict(sorted(obj.items()))
        new_step = "\n" + new_step
        res = "{" + new_step
        keys = list(obj)
        for i in keys[:-1]:
            res += step + '"' + str(i) + '"' + ": " + Json._dumps(obj[i], step,
                                                                  new_step.replace('\n', '') + step) + "," + new_step
        res += step + '"' + str(keys[-1]) + '"' + ": " + Json._dumps(obj[keys[-1]], step,
                                                                     new_step.replace('\n', '') + step) + new_step + "}"
        return res

    @staticmethod
    def dump(obj, fp, sort_keys=False, indent=None):
        try:
            with open(fp, 'w') as file:
                file.write(Json.dumps(obj, sort_keys, indent))
        except FileNotFoundError:
            raise FileNotFoundError("file doesn't exist")

    @staticmethod
    def dumps(obj, sort_keys=False, indent=None):
        Json.func_found = {}
        Json.sort = sort_keys
        if isinstance(indent, int) and indent > 0:
            step = " " * indent
            res = Json._dumps(obj, step)
            if indent < 1:
                res = res.replace("\n", "")
        else:
            res = Json._dumps(obj).replace("\n", "")
        return res

    @staticmethod
    def load(fp):
        try:
            with open(fp, 'r') as file:
                data = file.read()
        except FileNotFoundError:
            raise FileNotFoundError("file doesn't exist")
        return Json.loads(data)

    @staticmethod
    def loads(string):
        index = 0
        try:
            while string[index] == ' ' or string[index] == '\n':
                index += 1
        except IndexError:
            pass

        if string[index] == '"':
            obj, index = Json.parse_string(string, index + 1)
        elif string[index].isdigit() or (string[index] == '-' and string[index + 1].isdigit()):
            obj, index = Json.parse_digit(string, index)
        elif string[index] == '{':
            obj, index = Json.parse_dict(string, index + 1)
        elif string[index] == '[':
            obj, index = Json.parse_array(string, index + 1)
        elif string[index] == 'n' and string[index:index + 4] == 'null':
            obj = None
            index += 4
        elif string[index] == 't' and string[index:index + 4] == 'true':
            obj = True
            index += 4
        elif string[index] == 'f' and string[index:index + 5] == 'false':
            obj = False
            index += 5
        elif string[index] == 'N' and string[index:index + 3] == 'NaN':
            obj = False
            index += 3
        elif string[index] == 'I' and string[index:index + 8] == 'Infinity':
            obj = float('Infinity')
            index += 8
        elif string[index] == '-' and string[index:index + 9] == '-Infinity':
            obj = float('-Infinity')
            index += 9
        else:
            raise StopIteration(index)

        try:
            while True:
                if string[index] != ' ' and string[index] != '\n':
                    raise StopIteration(index)
                index += 1
        except IndexError:
            pass

        return obj
