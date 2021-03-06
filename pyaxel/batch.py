# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 10:36:25 2018

@author: Fotonica
"""

import numpy as np

from pint import UnitRegistry

from re import split, sub

from tkinter import Tk, filedialog

from enum import Enum, IntEnum, auto

import sys, os, errno
from os import listdir
from os import linesep
from os.path import normpath, join, abspath, splitext

ureg = UnitRegistry()
Q_ = ureg.Quantity

types = {"s": str,
         "f": float,
         "i": int,
         "b": bool,
         "q": Q_}

class PATH:
    def __init__(self):
        self.__name__ = "PATH"

class ATTR:
    def __init__(self, name):
        self.__name__ = "ATTR"
        self.name = str(name)

class FNVAR:
    def __init__(self, name):
        self.__name__ = "FNVAR"
        self.name = str(name)

class CALVAR:
    def __init__(self, name):
        self.__name__ = "CALVAR"
        self.name = str(name)

class REDVAR:
    def __init__(self, name):
        self.__name__ = "REDVAR"
        self.name = str(name)

class Array:
    def __init__(self, size, dtype=float):
        self.size = size
        self.dtype = dtype

class ErrorPolicies(IntEnum):
    STOP = auto()
    STOP_ON_REPEAT = auto()
    SKIP = auto()
    SILENT_SKIP = auto()

def split_path(path):
    from os.path import split, splitext
    
    folder, full_name = split(path)
    name, extension = splitext(full_name)
    
    return folder, name, extension, full_name

def validate_files(path_list):
    if isinstance(path_list, list):
        for path in path_list:
            with open(path, "r"):
                pass
    elif isinstance(path_list, str):
        with open(path_list, "r"):
            pass
    
    return path_list

def is_pathname_valid(pathname: str) -> bool:
    '''
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    '''
    
    ERROR_INVALID_NAME = 123
    
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
        # if any. Since Windows prohibits path components from containing `:`
        # characters, failing to strip this `:`-suffixed prefix would
        # erroneously invalidate all valid absolute Windows pathnames.
        _, pathname = os.path.splitdrive(pathname)

        # Directory guaranteed to exist. If the current OS is Windows, this is
        # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
        # environment variable); else, the typical root directory.
        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)   # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            # If an OS-specific exception is raised, its error code
            # indicates whether this pathname is valid or not. Unless this
            # is the case, this exception implies an ignorable kernel or
            # filesystem complaint (e.g., path not found or inaccessible).
            #
            # Only the following exceptions indicate invalid pathnames:
            #
            # * Instances of the Windows-specific "WindowsError" class
            #   defining the "winerror" attribute whose value is
            #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
            #   fine-grained and hence useful than the generic "errno"
            #   attribute. When a too-long pathname is passed, for example,
            #   "errno" is "ENOENT" (i.e., no such file or directory) rather
            #   than "ENAMETOOLONG" (i.e., file name too long).
            # * Instances of the cross-platform "OSError" class defining the
            #   generic "errno" attribute whose value is either:
            #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
            #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    # If a "TypeError" exception was raised, it almost certainly has the
    # error message "embedded NUL character" indicating an invalid pathname.
    except TypeError:
        return False
    # If no exception was raised, all path components and hence this
    # pathname itself are valid. (Praise be to the curmudgeonly python.)
    else:
        return True
    # If any other exception was raised, this is an unrelated fatal issue
    # (e.g., a bug). Permit this exception to unwind the call stack.

def get_fn_syntax_props(syntax):
    """
    Gets properties of filename variables indicated by syntax. Returns variable
    names and types and
    """
    
    syntax = split("<|>", syntax)
    var_specs = syntax[1::2]
    var_names = [""]*len(var_specs)
    var_types = [""]*len(var_specs)
    
    separators = [x for x in syntax[0::2] if x != ""]
    re_condition = "|".join(separators)
    
    for (i, var_spec) in enumerate(var_specs):
        var_spec = split(",", var_spec)
        var_names[i] = var_spec[0]
        
        if len(var_spec) > 1:
            if var_spec[1] in types:
                var_types[i] = types[var_spec[1]]
            else:
                raise TypeError("Type {} not allowed for parsing filename. Types allowed are {}.".format(var_spec[1], types))
        else:
            var_types[i] = "f"
    
    return var_names, var_types, re_condition

def parse_filename(filename, syntax):
    """
    Returns a dict where keys are variable names from the filename and
    values are their respective variable values.
    
    Usage:
        fn_vars = parse_filename(filename = 'Medicion_Tension=100V,Sentido=Positivo.csv',
                                       syntax = 'Tension=<Tension,q>,Sentido=<Sentido,s>')
                                                             ^    ^              ^     ^
                                                            name type           name  type
        returns a dictionary with following data:
            fn_vars = {'Tension': pint.Quantity(100, 'volt'),
                             'Sentido': str('Positivo')}
    """
    
    fn_vars_dict = {}
    
    var_names, var_types, re_condition = get_fn_syntax_props(syntax)
    var_values = [x for x in split(re_condition, filename) if x != ""]
    
    for var_name, var_value, var_type in zip(var_names, var_values, var_types):
        fn_vars_dict[var_name] = var_type(var_value)
    
    return fn_vars_dict

def file_dialog_open(title="Abrir archivo", initial_dir="/", filetypes=[("all files","*.*")], batch=False):
    tkroot = Tk()
    
    if batch:
        path = filedialog.askopenfilenames(title=title,
                                          initialdir=initial_dir,
                                          filetypes=filetypes)
    else:
        path = filedialog.askopenfilename(title=title,
                                          initialdir=initial_dir,
                                          filetypes=filetypes)
    tkroot.lift()
    tkroot.withdraw()
    
    if isinstance(path, tuple):
        path = list(path)
    else:
        path = [path]
    
    for idx in range(len(path)):
        path[idx] = normpath(path[idx])
    
    return path

def file_dialog_dir_open(title="Abrir directorio", initial_dir="/"):
    tkroot = Tk()
    
    path = filedialog.askdirectory(title=title,
                                   initialdir=initial_dir)
    tkroot.lift()
    tkroot.withdraw()
    
    return normpath(path)

def file_dialog_save(title="Guardar archivo", initial_dir="/", filetypes=[("all files","*.*")]):
    tkroot = Tk()
    
    path = filedialog.asksaveasfilename(title=title,
                                        initialdir=initial_dir,
                                        filetypes=filetypes)
    tkroot.lift()
    tkroot.withdraw()
    
    return normpath(path)


class Var:
    """
    Class for generic variables, consists of array of values indexed by file.
    Saves information about name, data type and length. Allows for subscript
    in the file-axis.
    
    """
    
    def __init__(self, name, dtype=object, value=None, length=1):
        self.name = name
        self.dtype = dtype
        
        if value is None:
            self._length = length
            self._value = self.initialize(length)
        else:
            self._value = value
            self._length = len(self._value)
    
    def __getitem__(self, key):
        return self.__class__(name=self.name, dtype=self.dtype, value=self._value[key])
    
    def __setitem__(self, key, value):
        self._value[key] = value
    
    def __call__(self):
        if self.length == 1:
            return self._value[0]
        else:
            return self._value
    
    def initialize(self, length):
        if isinstance(self.dtype, Array):
            size = (length, ) + self.dtype.size
            
            init = np.array(np.zeros(size, dtype=self.dtype.dtype), ndmin=1)
            return init
        elif isinstance(self.dtype, type):
            return np.array(np.zeros((length, ), dtype=self.dtype), ndmin=1)
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if not value:
            self._name = ""
        elif isinstance(value, str):
            self._name = value
        else:
            raise TypeError("Variable name must be string type.")
    
    @property
    def dtype(self):
        return self._dtype
    
    @dtype.setter
    def dtype(self, value):
        if not (isinstance(value, type) or isinstance(value, Array)):
            raise TypeError("Argument dtype must be a valid type.")
#        elif value is str:
#            value = object
        
        self._dtype = value
    
    @property
    def length(self):
        return len(self._value)
    
    @length.setter
    def length(self, value):
        if not isinstance(value, int):
            raise TypeError("Variable length must be int type.")
        
        if value == self.length:
            return
        elif value > self.length:
            self._value = np.append(self._value, self.initialize(value-self.length), axis=0)
        elif value < self.length:
            self._value = self._value[0:value]
    
    @property
    def value(self):
        if self.length == 1:
            return self._value[0]
        else:
            return self._value
    
    @value.setter
    def value(self, value):
        if isinstance(self.dtype, type):
            if self.dtype == str:
                dtype = object
            else:
                dtype = self.dtype
        elif isinstance(self.dtype, Array):
            dtype = self.dtype.dtype
        
        value = np.array(value, ndmin=1).astype(dtype)
        self._value = value


class VarGroup:
    """
    Groups of Var objects, all with same length along the file-axis. Individual
    variables can be accessed by name subscript. Also allows for subscripts
    along file-axis, returning a "croped" new VarGroup object.
    
    Examples:
        vg = VarGroup(Var1, Var2, ..., VarN)
            
            where Var1, ..., VarN are Var objects with same length
        
        vg = VarGroup.from_props(names=["x","t"], dtypes=float, length=10)
        vg = VarGroup.from_props(names=["gender","age"], dtypes=[str, int], length=1)
    
    """
    
    def __init__(self, *vars):
        # Initiate by vars:
        self._vars = {}
        
        self._length = self.validate_lengths(*vars)
        
        for var in vars:
            if isinstance(var, Var):
                self._vars[var.name] = var
            else:
                raise TypeError("All variables must be Var type.")
    
    @classmethod
    def from_props(cls, names, dtypes=[object], length=0):
        names = list(names)
        dtypes = list(dtypes)
        length = int(length)
        
        if len(dtypes) == 1:
            dtypes = dtypes * len(names)
        else:
            if len(dtypes) != len(names):
                raise ValueError("Variable names and data types must have same length.")
        
        vars = []
        for name, dtype in zip(names, dtypes):
            vars.append(Var(name, dtype, length=length))
        
        return cls(*tuple(vars))
    
    @classmethod
    def copy(cls, var_group, length=None):
        if not length:
            length = var_group.length
        
        return VarGroup.from_props(var_group.names, var_group.dtypes, length=length)
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return self._vars[key]
        elif isinstance(key, int) or isinstance(key, slice):
            new_vars = []
            
            for var in self._vars.values():
                new_vars.append(var[key])
            
            return self.__class__(*tuple(new_vars))
    
    def __setitem__(self, key, value):
        if isinstance(key, str):
            self._vars[key].value = value
        elif isinstance(key, (int, slice)):
            if not isinstance(value, VarGroup):
                raise TypeError("Assignement of variable group value must take a VarGroup object.")
            
            for var_key in self._vars.keys():
                if self.length == 1:
                    self._vars[var_key].value = value[var_key].value
                elif self.length > 1:
                    self._vars[var_key].value[key] = value[var_key].value
        else:
            raise KeyError("Variable group assignement key must be either string of a variable name or a integer or slice.")
    
    def __iter__(self):
        return iter(self._vars.values())
    
    def __repr__(self):
        string = (linesep + " ").join(["'{}': {}".format(key, val.value.__repr__()) for key,val in self._vars.items()])
        string = "{" + string + "}"
        
        return string
    
    @property
    def length(self):
        return self._length
    
    @length.setter
    def length(self, value):
        # If new value is the same as before, do nothing
        if value == self.length:
            return
        # Else, change all lengths
        else:
            self._length = value
            for var_name in self._vars.keys():
                self._vars[var_name].length = value
    
    @property
    def nvars(self):
        return len(self._vars)
    
    @property
    def names(self):
        return [var.name for var in self._vars.values()]
    
    @property
    def dtypes(self):
        return [var.dtype for var in self._vars.values()]
    
    def unpack(self):
        if self.nvars == 1:
            return tuple(var.value for var in self._vars.values())[0]
        else:
            return tuple(var.value for var in self._vars.values())
    
    @staticmethod
    def validate_lengths(*vars):
        lengths = [var.length for var in vars]
        condition = [x==lengths[0] for x in lengths]
        
        if not all(condition):
            raise ValueError("All variables must have same length.")
        
        return lengths[0]


class FNSyntax:
    """
    Class for filename parsing. Filename variables are assigned as Var objects.
    Automatically constructs conditions as regular expresions for filename
    parsing.
    
    Usage:
        
        fn_syntax = FNSyntax("date=", Var(name="Date", dtype=str),
                             ", current=", Var(name="Current", dtype=float)
                             "mA.txt")
        
        fn_vars = fn_syntax.parse_filename("date=2019-04-02, current=120mA.txt")
    
    """
    
    def __init__(self, *args):
        is_right_type = [(isinstance(arg, str) or isinstance(arg, Var)) for arg in args]
        
        if not all(is_right_type):
            raise TypeError("Argument of filename syntax object constructor must be a tuple of strings and Var objects.")
        
        vars = [var for var in args if isinstance(var, Var)]
        self.vars = VarGroup(*tuple(vars))
        
        self.re_conditions = dict()
        
        for idx, arg in enumerate(args):
            if isinstance(arg, Var):
                leading_condition = "".join([arg if isinstance(arg, str) else ".*" for arg in args[0:idx]])
                trailing_condition = "".join([arg if isinstance(arg, str) else ".*" for arg in args[idx+1:]])
                
                full_condition = "|".join([leading_condition, trailing_condition])
                self.re_conditions[arg.name] = full_condition
    
    def parse_filename(self, filename):
        """
        Parses filename as determined by its syntax. Returns a VarGroup object
        of length 1 with Var variables that matches names and data types with
        those given at initialization.
        
        Arguments:
            filename: str
                file name to be parsed
        
        Returns:
            fn_vars: VarGroup
                VarGroup object which collects all the parsed values in Var
                objects with matching names and datatypes.
        
        Usage:
            fn_syntax = FNSyntax("date=", Var(name="Date", dtype=str),
                                 ", current=", Var(name="Current", dtype=float)
                                 "mA.txt")
            
            fn_vars = fn_syntax.parse_filename("date=2019-04-02, current=120mA.txt")
        
        """
        
        fn_vars = VarGroup.from_props(names=self.vars.names, dtypes=self.vars.dtypes, length=1)
        
        for idx, var in enumerate(self.vars):
            try:
                fn_vars[var.name] = "".join(split(self.re_conditions[var.name], filename))
            except Exception as e:
                string = "Falied to parse filename '{}' for variable '{}' with condition '{}'. Original exception was:".format(filename, var.name, self.re_conditions[var.name]) + linesep + linesep
                string += "{}: {}".format(e.__class__.__name__, e)
                raise ValueError(string)
        
        return fn_vars


class File:
    
    def __init__(self, path=None, fn_syntax=None):
        self._path = ""
        self._folder = ""
        self._full_name = ""
        self._name = ""
        self._extension = ""
        self._fn_syntax = None
        
        if path == None:
            self.path = file_dialog_open(batch=False)[0] # file_dialog_open always returns a list
        else:
            self.path = validate_files(path)
        
        self.fn_syntax = fn_syntax
    
    def __repr__(self):
        return "File('{}')".format(self.path, self.fn_syntax)
    
    @property
    def folder(self):
        return self._folder
    
    @property
    def full_name(self):
        return os.path
    
    @property
    def name(self):
        return self._name
    
    @property
    def extension(self):
        return self._extension
    
    @property
    def path(self):
        return self._path
    
    @path.setter
    def path(self, value):
        if not value:
            self._path = ""
            self._folder = ""
            self._name = ""
            self._extension = ""
        elif not isinstance(value, str):
            raise TypeError("File path must be a string with a valid path.")
        elif not validate_files(value):
            raise ValueError("Invalid file path")
        else:
            value = os.path.abspath(os.path.normpath(value))
            
            self._path = value
            self._folder, self._name, self._extension, self._full_name = split_path(value)
    
    @property
    def fn_syntax(self):
        return self._fn_syntax
    
    @fn_syntax.setter
    def fn_syntax(self, value):
        if isinstance(value, type(None)):
            self._fn_syntax = None
            self._fn_vars = None
        elif isinstance(value, FNSyntax):
            self._fn_syntax = value
            self._fn_vars = self._fn_syntax.parse_filename(self._full_name)
        else:
            raise TypeError("Filename syntax must be a FNSyntax object.")
    
    @property
    def fn_vars(self):
        return self._fn_vars

class FileGroup(object):
    
    def __init__(self, files=None, fn_syntax=None):
        self.clear()
        
        if files is None:
            self.files = file_dialog_open(batch=True)
        else:
            self.files = files
        
        self.fn_syntax = fn_syntax
    
    def __iter__(self):
        self.iter = 0
        return self
    
    def __next__(self):
        if self.iter < self.length:
            self.iter += 1
            return self.files[self.iter-1]
        else:
            raise StopIteration
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.files[key]
        elif isinstance(key, slice) or isinstance(key, np.ndarray):
            return self.__class__(files=self.files[key], fn_syntax=self.fn_syntax)
        else:
            raise KeyError("File group subscript must be either int or slice type.")
    
    def __setitem__(self, key, value):
        if isinstance(key, int) or isinstance(key, slice):
            self.files[key] = value
        else:
            raise KeyError("File group assignement key must be either int or slice type.")
    
    @classmethod
    def from_directory(cls, path=None, extension=None, fn_syntax=None):
        # Convert extension to list
        if isinstance(extension, type(None)):
            extension = []
        elif isinstance(extension, str):
            extension = [extension]
        elif isinstance(extension, list):
            pass
        else:
            raise TypeError("Extension must be a string or a list of strings.")
        
        # Remove dots from extensions:
        for idx, ext in enumerate(extension):
            if ext[0] == ".":
                extension[idx] = extension[idx][1:]
        
        # Add files
        all_files = listdir(path)
        files = []
        
        for file in all_files:
            # If no given extension, add all files
            if not extension:
                files.append(join(path, file))
            # If an extension list is given, filter by extension
            else:
                this_ext = splitext(file)[1][1:] # Get extension without dot
                if this_ext in extension:
                    files.append(join(path, file))
        
        return cls(files=files, fn_syntax=fn_syntax)
    
    @property
    def paths(self):
        return self._paths
    
    @paths.setter
    def paths(self, value):
        if isinstance(value, type(None)):
            self.clear()
        if isinstance(value, list) or isinstance(value, str) or isinstance(value, File):
            self.clear()
            self.append(value)
    
    @property
    def files(self):
        return self._files
    
    @files.setter
    def files(self, value):
        if isinstance(value, type(None)):
            self.clear()
        elif isinstance(value, np.ndarray) or isinstance(value, list) or isinstance(value, str) or isinstance(value, File):
            self.clear()
            self.append(value)
        else:
            raise TypeError("Files must be either a valid path string, a list of paths or a File object")
    
    @property
    def length(self):
        return len(self.files)
    
    @property
    def fn_syntax(self):
        return self._fn_syntax
    
    @fn_syntax.setter
    def fn_syntax(self, value):
        if not value:
            value = None
        elif isinstance(value, tuple):
            self._fn_syntax = FNSyntax(*value)
        elif isinstance(value, FNSyntax):
            self._fn_syntax = value
        else:
            raise TypeError("Filename syntax must be FNSyntax type.")
        
        for file in self.files:
            file.fn_syntax = self._fn_syntax
        
        self._fn_vars = self.collect_fn_vars()
    
    def collect_fn_vars(self):
        if self.fn_syntax is None:
            return None
        else:
            fn_vars = VarGroup.copy(self.fn_syntax.vars, length=self.length)
            
            for idx, file in enumerate(self.files):
                fn_vars[idx] = file.fn_vars
            
            return fn_vars
    
    @property
    def fn_vars(self):
        return self._fn_vars
    
    def append(self, files):
        # Verify if all elements from files are File objects or strings
        if files is None:
            return None
        if isinstance(files, list) or isinstance(files, np.ndarray):
            if not all([isinstance(x, str) or isinstance(x, File) for x in files]):
                raise TypeError("File list must be a list of File objects or strings with valid paths")
        else:
            raise TypeError("File list must be a list of File objects or strings with valid paths")
        
        for value in files:
            if isinstance(value, str):
                value = File(path=value)
            
            self._files = np.append(self._files, value)
            self._paths = np.append(self.files, value.path)
    
    def clear(self):
        self._files = np.array([], dtype=object, ndmin=1)
        self._paths = np.array([], dtype=object, ndmin=1)
        self._fn_syntax = None


class BatchTask:
    """
    Main class for performing batch tasks.
    
    Arguments of __init__:
        files: list or FileGroup object
            Either a list of file paths (as strings) or a FileGroup object
            pointing to all target files. Note that, when passing file paths as
            strings, a list must be provided even for a single file.
        fn_syntax: tuple or FNSyntax
            Filename syntax passed either as a FNSyntax object or as a tuple
            that can be used for FNSyntax object initialization. If a FileGroup
            was passed in the 'files' argument and it already has a filename
            syntax specified, this argument is ignored.
        callback: Python callable
            Callback function that will be called for each file. Its returns
            will maped as callback_vars specifies and its arguments will be
            passed as *args and **kwargs specifies (see below)
        callback_vars: tuple or VarGroup
            Return variables of callback function, passed either as a VarGroup
            object or a tuple which can be used for VarGroup object
            initialization. The values returned by callback for each call will
            be stored in this VarGroup object in the order they are specified.
        *args and **kwargs: tuple and map
            Arguments and keyword-arguments that will be passed to callback.
            They can be any Python object. When a PATH instance is specified in
            any position, the path of the file under processing is inserted in
            those positions at every callback call. When a FNVAR instance
            (which has a specified name) is passed in any position, the value
            of the filename variable that matches the specified name will be
            inserted in that position at every callback call.
    
    Usage:
        # Let's process the file named 'user=Pablo,age=10.txt' with the
        # function 'is_underage' defined below.
        
        def is_underage(path, user, age, do_print):
            is_underage = age < 18
            
            if do_print:
                print("{} is {}".format(user, 'underage' if is_underage else 'not underage')
            
            return path, is_underage
        
        fg = FileGroup(['user=Pablo,age=10.txt'])
        fn_syntax = FNSyntax("user=", Var("User", str), ",age=", Var("Age", float), ".txt")
        
        callback_vars = VarGroup(Var("Path", str), Var("Is Underage", bool))
        
        bt = BatchTask(fg,    # files to be processed
                       fn_syntax,    # filename syntax
                       is_underage,    # callback function
                       callback_vars,    # output variables
                       PATH(), FNVAR("User"), age=FNVAR("Age"), do_print=True    # arguments and keyword-arguments to be passed to callback function
                       )
        bt.run()
        
        print(bt.callback_vars)
        print(bt.callback_vars["Is Underage"].value)
        
    """
    
    class ErrorPolicy:
        def __init__(self, policy, exception_name=None):
            if isinstance(policy, str):
                self.policy = ErrorPolicies[policy.upper()]
            elif isinstance(policy, int):
                self.policy = ErrorPolicies(policy)
            elif isinstance(policy, type(ErrorPolicies(1))):
                self.policy = policy
            else:
                raise TypeError("Argument 'policy' must be a string or a ErrorPolicies enum item. See 'Batch.ErrorPolicies'.")
            
            if not exception_name:
                self.exception_name = []
            elif isinstance(exception_name, str):
                self.exception_name = [exception_name]
            elif isinstance(exception_name, list):
                self.exception_name = []
                
                for name in exception_name:
                    if isinstance(name, str):
                        self.exception_name.append(name)
                    else:
                        raise TypeError("Exception name must be a string or a list of strings.")
            else:
                raise TypeError("Exception name must be eithr a string or a list of strings.")
    
    def __init__(
            self, files,
            fn_syntax=None,
            callback=None,
            callback_args=None,
            callback_kwargs=None,
            callback_vars=None,
            reduction=None,
            reduction_args=None,
            reduction_kwargs=None,
            reduction_vars=None,
            keep_callback_returns=None
            ):
        
        self.files = files
        if fn_syntax:
            self.files.fn_syntax = fn_syntax
        self.fn_vars = self.files.fn_vars
            
        self.callback = callback
        self.callback_args = callback_args
        self.callback_kwargs = callback_kwargs
        self.callback_vars = callback_vars
        
        self.reduction = reduction
        self.reduction_args = reduction_args
        self.reduction_kwargs = reduction_kwargs
        self.reduction_vars = reduction_vars
        
        self.error_policy = ErrorPolicies.STOP
        
        # If keep_callback_returns is not specified, set its value according to
        # if there is a reduction method assigned or not
        if not (keep_callback_returns is None):
            self.keep_callback_returns = keep_callback_returns
        else:
            self.keep_callback_returns = not bool(self.reduction)
    
    @property
    def files(self):
        return self._files
    
    @files.setter
    def files(self, value):
        if isinstance(value, list):
            self._files = FileGroup(value)
        elif isinstance(value, FileGroup):
            self._files = value
        else:
            raise TypeError("File list must be either a FileGroup object or a list of paths or File objects")
    
    @property
    def length(self):
        return self.files.length
    
    @property
    def keep_callback_returns(self):
        return self._keep_callback_returns
    
    @keep_callback_returns.setter
    def keep_callback_returns(self, value):
        if not isinstance(value, bool):
            return TypeError("Keep callback returns value must be bool type.")
        
        self._keep_callback_returns = value
        
        if value:
            self.callback_vars.length = self.length
        else:
            self.callback_vars.length = 1
    
    @property
    def error_policy(self):
        return self._error_policy
    
    @error_policy.setter
    def error_policy(self, value):
        if isinstance(value, type(ErrorPolicies(1))):
            self._error_policy = self.ErrorPolicy(value)
        elif isinstance(value, str):
            self._error_policy = self.ErrorPolicy(value)
        elif isinstance(value, int):
            self._error_policy = self.ErrorPolicy(value)
        elif isinstance(value, self.ErrorPolicy):
            self._error_policy = value
        else:
            raise TypeError("Error policy must be either a string, an integer, an ErrorPolicy object or an ErrorPolicies item.")
        
        self._last_error = None
        self._files_with_errors = {"paths": [],
                                   "indices": []}
    
    @property
    def files_with_errors(self):
        return self._files_with_errors
    
    @property
    def callback_vars(self):
        return self._callback_vars
    
    @callback_vars.setter
    def callback_vars(self, value):
        if value is None:
            self._callback_vars = VarGroup.from_props(names=["output"], dtypes=[type(None)], length=self.length)
        elif isinstance(value, VarGroup):
            self._callback_vars = value
            self._callback_vars.length = self.length
        elif isinstance(value, Var):
            self._callback_vars = VarGroup(value)
            self._callback_vars.length = self.length
        elif isinstance(value, tuple):
            self._callback_vars = VarGroup(*value)
            self._callback_vars.length = self.length
        else:
            raise TypeError("Output variables argument must be either VarGroup type or a tuple with Var objects.")
    
    @property
    def reduction_vars(self):
        return self._reduction_vars
    
    @reduction_vars.setter
    def reduction_vars(self, value):
        if value is None:
            self._reduction_vars = VarGroup.from_props(names=["reduction"], dtypes=[type(None)], length=1)
        elif isinstance(value, VarGroup):
            self._reduction_vars = value
            self._reduction_vars.length = 1
        elif isinstance(value, Var):
            self._reduction_vars = VarGroup(value)
            self._reduction_vars.length = 1
        elif isinstance(value, tuple):
            self._reduction_vars = VarGroup(*value)
            self._reduction_vars.length = 1
        else:
            raise TypeError("Reduction variables argument must be either VarGroup type or a tuple with Var objects.")
    
    def set_callback(self, function, args=None, kwargs=None, return_vars=None, keep_callback_returns=None):
        self.callback = function
        self.callback_args = args
        self.callback_kwargs = kwargs
        self.callback_vars = return_vars
        
        if not (keep_callback_returns is None):
            self.keep_callback_returns = not bool(self.reduction)
    
    def set_reduction(self, function, args=None, kwargs=None, return_vars=None, keep_callback_returns=False):
        self.reduction = function
        self.reduction_args = args
        self.reduction_kwargs = kwargs
        self.reduction_vars = return_vars
        
        if not (keep_callback_returns is None):
            self.keep_callback_returns = not bool(self.reduction)
    
    def insert_args(self, args, file_index):
        if args:
            args = list(args)
        else:
            args = []
        
        for index, arg in enumerate(args):
            if isinstance(arg, PATH) or (isinstance(arg, type) and arg.__name__ == "PATH"):
                args[index] = self.files[file_index].path
            if isinstance(arg, ATTR) or (isinstance(arg, type) and arg.__name__ == "ATTR"):
                args[index] = self.__getattribute__(arg.name)
            if isinstance(arg, FNVAR) or (isinstance(arg, type) and arg.__name__ == "FNVAR"):
                args[index] = self.files[file_index].fn_vars[arg.name].value
            if isinstance(arg, CALVAR) or (isinstance(arg, type) and arg.__name__ == "CALVAR"):
                args[index] = self.callback_vars[file_index][arg.name].value
            if isinstance(arg, REDVAR) or (isinstance(arg, type) and arg.__name__ == "REDVAR"):
                args[index] = self.reduction_vars[arg.name].value
        
        return tuple(args)
    
    def insert_kwargs(self, kwargs, file_index):
        if kwargs:
            kwargs = dict(kwargs)
        else:
            kwargs = {}
        
        for index, (key, value) in enumerate(kwargs.items()):
            if isinstance(value, PATH):
                kwargs[key] = self.files[file_index].path
            if isinstance(value, ATTR):
                kwargs[key] = self.__getattribute__(value.name)
            if isinstance(value, FNVAR):
                kwargs[key] = self.files[file_index].fn_vars[value.name].value
            if isinstance(value, CALVAR):
                kwargs[key] = self.callback_vars[file_index][value.name].value
            if isinstance(value, REDVAR):
                kwargs[key] = self.reduction_vars[value.name].value
        
        return kwargs
    
    def call(self, function, args, kwargs, return_vars):
        return_vars = VarGroup.copy(return_vars, length=1)
        ret = function(*args, **kwargs)
        
        if return_vars.nvars == 1:
            ret = (ret, )
        
        for position, key in enumerate(return_vars._vars.keys()):
            return_vars[key] = ret[position]
        
        return return_vars
    
    def handle_error(self, exception, file, file_idx):
        exception_name = exception.__class__.__name__
        
        if self.error_policy.policy == ErrorPolicies.STOP:
            # Will only stop if exception name matches specified exception_name
            if exception_name in self.error_policy.exception_name or not self.error_policy.exception_name:
                self._last_error = exception.__class__.__name__
                self._files_with_errors["paths"].append(file.path)
                self._files_with_errors["indices"].append(file_idx)
                
                raise exception
            else:
                print(exception)
        
        elif self.error_policy.policy == ErrorPolicies.STOP_ON_REPEAT:
            # Will only stop if exception name matches specified exception_name
            # and that exception was raised before
            if exception_name in self.error_policy.exception_name or not self.error_policy.exception_name:
                last_error = self._last_error
                self._last_error = exception_name
                self._files_with_errors["paths"].append(file.path)
                self._files_with_errors["indices"].append(file_idx)
                
                if last_error == exception_name:
                    raise exception
            else:
                print(exception)
        
        elif self.error_policy.policy == ErrorPolicies.SKIP:
            # Will skip exceptions that matches matches exception_name
            if exception_name in self.error_policy.exception_name or not self.error_policy.exception_name:
                self._last_error = exception_name
                self._files_with_errors["paths"].append(file.path)
                self._files_with_errors["indices"].append(file_idx)
                print(exception)
            else:
                raise exception
        
        elif self.error_policy.policy == ErrorPolicies.SILENT_SKIP:
            # Will skip exceptions that matches matches exception_name
            if exception_name in self.error_policy.exception_name or not self.error_policy.exception_name:
                self._last_error = exception_name
                self._files_with_errors["paths"].append(file.path)
                self._files_with_errors["indices"].append(file_idx)
            else:
                raise exception
    
    def run(self):
        for idx, file in enumerate(self.files):
            print("Processing file {} of {}: {}'{}'".format(idx+1, self.files.length, os.linesep, file.path) + linesep)
            
            # Main callback
            callback_args = self.insert_args(self.callback_args, idx)
            callback_kwargs = self.insert_kwargs(self.callback_kwargs, idx)
            
            this_idx = idx if self.keep_callback_returns else 0 # Override index to override callback returns
            
            try:
                self.callback_vars[this_idx] = self.call(function=self.callback,
                                                         args=callback_args,
                                                         kwargs=callback_kwargs,
                                                         return_vars=self.callback_vars)
            except Exception as exception:
                self.handle_error(exception, file, idx)
                
            try:
                if self.reduction:
                    reduction_args = self.insert_args(self.reduction_args, this_idx)
                    reduction_kwargs = self.insert_kwargs(self.reduction_kwargs, this_idx)
                    
                    self.reduction_vars = self.call(function=self.reduction,
                                                    args=reduction_args,
                                                    kwargs=reduction_kwargs,
                                                    return_vars=self.reduction_vars)
            except Exception as exception:
                self.handle_error(exception, file, idx)


if __name__ == "__main__":
    
    fn_syntax = FNSyntax("2019-03-18_",
                         Var("Mode", str), "_",
                         Var("Wavelength", float), "nm,",
                         Var("ExpTime"), "ms,",
                         Var("Power", float), "uW.txt")
    
    fg = FileGroup.from_directory(path="E:\\Axel (Google Drive)\Proyecto OCT\\2019-02-05_Calibracion_espectrometro\\2019-03-18_Calibracion_CW\\prueba",
                                  fn_syntax=fn_syntax)
    
    def callback(path, mode, wavelength, exptime, power):
        return path, mode, wavelength, exptime, power
    
    def reduction(length, red_wavelength, red_exptime, red_power, wavelength, exptime, power):
        red_wavelength += wavelength/length
        red_exptime += exptime/length
        red_power += power/length
        
        return red_wavelength, red_exptime, red_power
    
    bt = BatchTask(files=fg)
    bt.set_callback(callback,
                    args=(PATH(), FNVAR("Mode")),
                    kwargs={"wavelength": FNVAR("Wavelength"), "exptime": FNVAR("ExpTime"), "power": FNVAR("Power")},
                    return_vars=(Var("Path", str), Var("Mode", str), Var("Wavelength", float), Var("ExpTime", float), Var("Power", float)))
    
    bt.set_reduction(reduction,
                     args=(ATTR("length"), REDVAR("Wavelength"), REDVAR("ExpTime"), REDVAR("Power")),
                     kwargs={"wavelength": CALVAR("Wavelength"), "exptime": CALVAR("ExpTime"), "power": CALVAR("Power")},
                     return_vars=(Var("Wavelength", float), Var("ExpTime", float), Var("Power", float)))
    
    bt.error_policy = bt.ErrorPolicy("stop_on_repeat", ["AttributeError"])
    
    bt.run()
    
    print(bt.callback_vars)
    print(bt.reduction_vars)
    




