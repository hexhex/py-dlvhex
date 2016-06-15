from types import ModuleType
from typing import Any, Iterable, MutableMapping, Optional, Union
from .solver import Solver, Results
from .input import InputSpecification  # flake8: noqa
from .output import OutputSpecification  # flake8: noqa
from .parser import parse_embedded_spec
from .registry import Constructor, Registry, LocalRegistry

__all__ = ['Program']


class Program:
    '''Represents an answer set program.'''

    def __init__(self, *, filename: Optional[str] = None, code: Optional[str] = None) -> None:
        '''Initialize an answer set program.

        For convenience, calls the appropriate `append...` method with the given `filename` and `code` keyword arguments.
        '''
        self.file_parts = []  # type: List[str]
        self.code_parts = []  # type: List[str]
        self.input_spec = None  # type: Optional[InputSpecification]
        self.output_spec = None  # type: Optional[OutputSpecification]
        self.solver = None  # type: Solver
        self.local_registry = LocalRegistry()  # type: Registry
        if filename is not None:
            self.append_file(filename)
        if code is not None:
            self.append_code(code)

    def parse_spec(self, code: str) -> None:
        i, o = parse_embedded_spec(code)
        if i is not None:
            if self.input_spec is None:
                self.input_spec = i
            else:
                raise ValueError("Only one INPUT specification per program is allowed.")
        if o is not None:
            if self.output_spec is None:
                self.output_spec = o
            else:
                raise ValueError("Only one OUTPUT specification per program is allowed.")

    def append_file(self, filename: str, *, parse_io_spec: bool = True) -> None:
        '''Append ASP code contained in the given file to the program.

        Note that unless the `parse_io_spec` argument is `False`, the file is opened immediately to extract any embedded I/O specifications.
        The file path is passed to the solver that will read the actual ASP code at the time of solving.
        '''
        self.file_parts.append(filename)
        if parse_io_spec:
            encoding = self.solver.encoding if self.solver is not None else Solver.default_encoding
            with open(filename, 'rt', encoding=encoding) as file:
                self.parse_spec(file.read())

    def append_code(self, code: str, *, parse_io_spec: bool = True) -> None:
        '''Append the given ASP code to the program.

        Unless the `parse_io_spec` argument is `False`, any embedded I/O specifications are extracted from the given string.
        '''
        self.code_parts.append(code)
        if parse_io_spec:
            self.parse_spec(code)

    def register(self, name: str, constructor: Constructor, *, replace: bool = False) -> None:
        self.local_registry.register(name, constructor, replace=replace)

    def import_from_module(self, names: Iterable[str], module_or_module_name: Union[ModuleType, str], package: Optional[str] = None) -> None:
        self.local_registry.import_from_module(names, module_or_module_name, package)

    # TODO: We need some facility to correctly map class names for output
    # TODO: Also provide a @classmethod for registering (even though it introduces evil global state... Program should make a copy of the current global state when it is registered?)
    # def register(self, name: str, constructor: Any) -> None:
    #     pass
    # def import_(self, module: str) -> None:
    #     pass

    # TODO: Maybe remove .solve and only use .__call__?
    def solve(self, *input_arguments, solver: Solver = None, cache: bool = False) -> Results:
        '''Solve the ASP program with the given input arguments and return a collection of answer sets.'''
        # TODO: Also allow to pass input arguments as keyword arguments, with names as defined in the input spec
        solver = solver or self.solver or Solver()
        return solver.run(self, input_arguments, cache=cache)

    def __call__(self, *args, **kwargs):
        '''Shorthand for the solve method.'''
        return self.solve(*args, **kwargs)
