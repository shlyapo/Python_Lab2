from abc import ABC, abstractmethod


class Serializer(ABC):
    @abstractmethod
    def dump(self, obj, file_format):
        pass

    @abstractmethod
    def dumps(self, obj):
        pass

    @abstractmethod
    def load(self, fp):
        pass

    @abstractmethod
    def loads(self, s):
        pass
