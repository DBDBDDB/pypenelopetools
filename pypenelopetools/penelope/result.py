""""""

# Standard library modules.
import abc
import re

# Third party modules.

# Local modules.

# Globals and constants variables.

PATTERN_NUMBER = re.compile(r'\d\.\d*E[\+\-]\d\d')

class _PenelopeResultBase(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def read(self, fileobj):
        raise NotImplementedError

    def _read_until_line_startswith(self, fileobj, prefix):
        line = fileobj.readline()
        if not line:
            raise EOFError('Read until EOF, no line with prefix {0}'.format(prefix))

        line = line.strip()
        if line.startswith(prefix):
            return line

        return self._read_until_line_startswith(fileobj, prefix)

    def _read_until_end_of_comments(self, fileobj):
        """
        Read until the end of the comments. 
        The next line returns by the file-object will be a non-comment line.
        """
        offset = fileobj.tell()
        line = fileobj.readline()
        if not line:
            raise EOFError('Read until EOF')

        line = line.strip()
        if line.startswith('#'):
            return self._read_until_end_of_comments(fileobj)

        fileobj.seek(offset)

    def _read_all_values(self, line):
        return [float(v) for v in PATTERN_NUMBER.findall(line)]

    @abc.abstractmethod
    def read_directory(self, dirpath):
        raise NotImplementedError
