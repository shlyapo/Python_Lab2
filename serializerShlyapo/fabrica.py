from serializerShlyapo.parser import json_parser, tom_parserl, yaml_parser


serializers = {
    "json": json_parser.Json,
    "toml": tom_parserl.Toml,
    "yaml": yaml_parser.Yaml
}


class Factory(object):
    @staticmethod
    def create_serializer(file_format: str):
        serializer = serializers.get(file_format.lower(), None)
        return serializer
