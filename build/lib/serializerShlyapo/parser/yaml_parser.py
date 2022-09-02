from serializerShlyapo.abstract import Serializer
from yaml import dump as dumps, full_load as loads


class Yaml(Serializer):
    @staticmethod
    def dumps(obj) -> str:
        return dumps(obj)

    @staticmethod
    def dump(obj, file="testyaml.yaml"):
        with open(file, 'w+') as fw:
            dumps(obj, fw)

    @staticmethod
    def loads(obj: str):
        return loads(obj)

    @staticmethod
    def load(file="testyaml.yaml"):
        with open(file, 'r+') as fr:
            return loads(file)
