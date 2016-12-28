"""
Definition of base keyword classes
"""

# Standard library modules.
import abc

# Third party modules.

# Local modules.
from pypenelopetools.penelope.base import _InLineBase
from pypenelopetools.pengeom.module import Module

# Globals and constants variables.

#--- Abstract classes

class _KeywordBase(_InLineBase):

    def __str__(self):
        return self.name

    @abc.abstractmethod
    def set(self, *args):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self):
        raise NotImplementedError

    @abc.abstractmethod
    def copy(self):
        raise NotImplementedError

    @abc.abstractproperty
    def name(self):
        raise NotImplementedError

#--- Core classes

class Keyword(_KeywordBase):

    def __init__(self, name, comment=""):
        self._name = name
        self._comment = comment

    def read(self, line_iterator):
        line = line_iterator.peek()
        name, values, _comment = self._extract_name_values_comment(line)
        if name != self.name:
            return

        self.set(*values)
        next(line_iterator)

    def write(self, index_table):
        values = self.get()
        if None in values:
            return []

        return [self._create_line(self.name, values, self.comment)]

    @property
    def name(self):
        return self._name

    @property
    def comment(self):
        return self._comment

class KeywordGroup(_KeywordBase):

    @abc.abstractmethod
    def get_keywords(self):
        raise NotImplementedError

    def get(self):
        values = []

        for keyword in self.get_keywords():
            values.extend(keyword.get())

        return tuple(values)

    def copy(self):
        return self.__class__()

    def read(self, line_iterator):
        for keyword in self.get_keywords():
            keyword.read(line_iterator)

    def write(self, index_table):
        lines = []
        for keyword in self.get_keywords():
            lines += keyword.write(index_table)
        return lines

    @property
    def name(self):
        return self.get_keywords()[0].name

class KeywordSequence(_KeywordBase):

    def __init__(self, keyword):
        self._base_keyword = keyword
        self._keywords = []

    def add(self, *args):
        keyword = self._base_keyword.copy()
        keyword.set(*args)
        self._keywords.append(keyword)

    def pop(self, index):
        self._keywords.pop(index)

    def clear(self):
        self._keywords.clear()

    def set(self, *args):
        self.clear()
        self.add(*args)

    def get(self):
        return tuple(keyword.get() for keyword in self._keywords)

    def copy(self):
        return self.__class__(self._base_keyword.copy())

    def read(self, line_iterator):
        line = line_iterator.peek()
        name, _values, _comment = self._extract_name_values_comment(line)
        while name == self._base_keyword.name:
            self._base_keyword.read(line_iterator)
            self.add(*self._base_keyword.get())

            line = line_iterator.peek()
            name, _values, _comment = self._extract_name_values_comment(line)

        return True

    def write(self, index_table):
        lines = []
        for keyword in self._keywords:
            lines += keyword.write(index_table)
        return lines

    @property
    def name(self):
        return self._base_keyword.name

#--- Derived keywords

class SpecialType(metaclass=abc.ABCMeta):

    def __call__(self, value):
        return value

    def convert(self, value, index_table):
        return value

class _ModuleType(SpecialType):

    def __call__(self, value):
        if isinstance(value, Module):
            return value

        try:
            return int(value)
        except TypeError:
            raise TypeError("Value should be an integer or a Module")

    def convert(self, value, index_table):
        if isinstance(value, Module):
            value = index_table[value]
        return value

module_type = _ModuleType()

class _FilenameType(SpecialType):

    def __call__(self, value):
        value = str(value)

        if len(value) > 20:
            raise ValueError('Filename is too long. Maximum 20 characters')

        return value

filename_type = _FilenameType()

class TypeKeyword(Keyword):

    def __init__(self, name, types, comment=""):
        super().__init__(name, comment)
        self._types = tuple(types)
        self._values = tuple([None] * len(types))

    def set(self, *args):
        if len(args) != len(self._types):
            raise ValueError("Keyword {0} requires {1} values, {2} given"
                             .format(self.name, len(self._types), len(args)))

        values = []
        for type_, value in zip(self._types, args):
            if value is not None:
                value = type_(value)
            values.append(value)

        self._values = tuple(values)

    def get(self):
        return self._values

    def copy(self):
        return self.__class__(self.name, self._types, self.comment)

    def write(self, index_table):
        tmpvalues = self.get()
        if None in tmpvalues:
            return []

        values = []
        for type_, value in zip(self._types, tmpvalues):
            if hasattr(type_, 'convert'):
                value = type_.convert(value, index_table)
            values.append(value)

        return [self._create_line(self.name, values, self.comment)]

