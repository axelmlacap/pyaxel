# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 10:36:25 2018

@author: Fotonica
"""

import numpy as np

from pint import UnitRegistry

from re import split, sub

from tkinter import Tk, filedialog

import sys, os, errno
from os import listdir
from os import linesep
from os.path import normpath, join

ureg = UnitRegistry()
Q_ = ureg.Quantity

types = {"s": str,
         "f": float,
         "i": int,
         "b": bool,
         "q": Q_}

class PATH:
    pass

class FN_VAR:
    def __init__(self, name):
        self.name = str(name)

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
            self.value = np.zeros((length, ), dtype=self.dtype)
            self._length = length
        else:
            self.value = value
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
        if not isinstance(value, type):
            raise TypeError("Dtype must be a valid type.")
        elif value is str:
            value = object
        
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
            self._value = np.append(self._value, np.zeros((value-self.length, ), dtype=self.dtype))
        elif value < self.length:
            self._value = self._value[0:value-1]
    
    @property
    def value(self):
        if self.length == 1:
            return self._value[0]
        else:
            return self._value
    
    @value.setter
    def value(self, value):
        value = np.array(value, ndmin=1).astype(self.dtype)
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
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return self._vars[key]
        elif isinstance(key, int) or isinstance(key, slice):
            new_vars = []
            
            for var in self._vars.values():
                new_vars.append(var[key])
            
            return self.__class__(tuple(new_vars))
    
    def __setitem__(self, key, value):
        if isinstance(key, str):
            self._vars[key].value = value
        elif isinstance(key, int) or isinstance(key, slice):
            if not isinstance(value, VarGroup):
                raise TypeError("Assignement of variable group value must take a VarGroup object.")
            
            for var_key in self._vars.keys():
                self._vars[var_key]._value[key] = value[var_key].value
        else:
            raise KeyError("Variable group assignement key must be either string of a variable name or a integer or slice.")
    
    def __iter__(self):
        return iter(self._vars.values())
    
    def __repr__(self):
        string = "{"
        
        for key, val in self._vars.items():
            string += "'" + key + "': " + val.value.__repr__() + "," + linesep
        
        string += "}"
        
        return string
    
    @property
    def length(self):
        return self._length
    
    @length.setter
    def length(self, value):
        value = int(value)
        
        # If new value is the same as before, do nothing
        if value == self.length:
            return
        # Else, change all lengths
        else:
            for var_name in self._vars.keys():
                self._vars[var_name].length = value
            self._length = value
    
    @property
    def nvars(self):
        return len(self._vars)
    
    @property
    def names(self):
        return [var.name for var in self._vars.values()]
    
    @property
    def dtypes(self):
        return [var.dtype for var in self._vars.values()]
    
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
            except:
                raise ValueError("Falied to parse filename '{}' for variable '{}' with condition '{}'.".format(filename, var.name, self.re_conditions[var.name]))
        
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
        
        if not files:
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
    
    @classmethod
    def from_directory(cls, path=None, fn_syntax=None):
        if not path:
            path = file_dialog_dir_open()
        
        files = listdir(path)
        for idx in range(len(files)):
            files[idx] = join(path, files[idx])
        
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
        elif isinstance(value, list) or isinstance(value, str) or isinstance(value, File):
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
        fn_vars = self.fn_syntax.vars
        fn_vars.length = self.length
        
        for idx, file in enumerate(self.files):
            fn_vars[idx] = file.fn_vars
        
        return fn_vars
    
    @property
    def fn_vars(self):
        return self._fn_vars
    
    def append(self, files):
        # Verify if all elements from files are File objects or strings
        if not files:
            return None
        if isinstance(files, list):
            if not all([isinstance(x, str) or isinstance(x, File) for x in files]):
                raise TypeError("File list must be a list of File objects or strings with valid paths")
        else:
            raise TypeError("File list must be a list of File objects or strings with valid paths")
        
        for value in files:
            if isinstance(value, str):
                self._files.append(File(path=value))
                self._paths.append(self.files[-1].path)
            elif isinstance(value, File):
                self._files.append(value)
                self._paths.append(value.path)
    
    def clear(self):
        self._files = []
        self._paths = []
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
            will maped as output_vars specifies and its arguments will be
            passed as *args and **kwargs specifies (see below)
        output_vars: tuple or VarGroup
            Return variables of callback function, passed either as a VarGroup
            object or a tuple which can be used for VarGroup object
            initialization. The values returned by callback for each call will
            be stored in this VarGroup object in the order they are specified.
        *args and **kwargs: tuple and map
            Arguments and keyword-arguments that will be passed to callback.
            They can be any Python object. When a PATH instance is specified in
            any position, the path of the file under processing is inserted in
            those positions at every callback call. When a FN_VAR instance
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
        
        output_vars = VarGroup(Var("Path", str), Var("Is Underage", bool))
        
        bt = BatchTask(fg,    # files to be processed
                       fn_syntax,    # filename syntax
                       is_underage,    # callback function
                       output_vars,    # output variables
                       PATH(), FN_VAR("User"), age=FN_VAR("Age"), do_print=True    # arguments and keyword-arguments to be passed to callback function
                       )
        bt.run()
        
        print(bt.output_vars)
        print(bt.output_vars["Is Underage"].value)
        
    """
    
    def __init__(self, files, fn_syntax=None, callback=None, output_vars=None, *args, **kwargs):
        
        self.files = files
        if fn_syntax:
            self.files.fn_syntax = fn_syntax
        self.callback = callback
        self.callback_args = args
        self.callback_kwargs = kwargs
        self.output_vars = output_vars
    
    @property
    def output_vars(self):
        return self._output_vars
    
    @output_vars.setter
    def output_vars(self, value):
        if value is None:
            self._output_vars = VarGroup.from_props(name="return", dtype=type(None), length=self.length)
        if isinstance(value, VarGroup):
            self._output_vars = value
            self._output_vars.length = self.length
        elif isinstance(value, tuple):
            self._output_vars = VarGroup(*value)
            self._output_vars.length = self.length
        else:
            raise TypeError("Output variables argument must be either VarGroup type or a tuple with Var objects.")
    
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
    
    def run(self):
        for idx, file in enumerate(self.files):
            print("Processing file {} of {}: {}'{}'".format(idx+1, self.files.length, os.linesep, file.path) + linesep)
            
            callback_args = self.insert_callback_args(self.callback_args, file.path, file.fn_vars)
            callback_kwargs = self.insert_callback_kwargs(self.callback_kwargs, file.path, file.fn_vars)
            
            ret = self.callback(file.path, *callback_args, **callback_kwargs)
            
            if self.output_vars.nvars == 1:
                ret = [ret]
            
            for position, key in enumerate(self.output_vars._vars.keys()):
                self.output_vars[key]._value[idx] = ret[position]
    
    @staticmethod
    def insert_callback_args(callback_args, path, fn_vars):
        callback_args = list(callback_args)
        
        for index, arg in enumerate(callback_args):
            if isinstance(arg, PATH):
                callback_args[index] = path
            elif isinstance(arg, FN_VAR):
                callback_args[index] = fn_vars[arg.name].value
        
        return tuple(callback_args)
    
    @staticmethod
    def insert_callback_kwargs(callback_kwargs, path, fn_vars):
        callback_kwargs = dict(callback_kwargs)
        
        for index, (key, value) in enumerate(callback_kwargs.items()):
            if isinstance(value, PATH):
                callback_kwargs[key] = path
            elif isinstance(value, FN_VAR):
                callback_kwargs[key] = fn_vars[value.name].value
        
        return callback_kwargs
    
#    @staticmethod
#    def check_args(fn_vars, *args, **kwargs):
#        
#        for idx, arg in enumerate(args):
#            if isinstance(arg, Var):
#                if Var.name in fn_vars.keys():
#                    args[idx] = fn_vars[arg.name][]





if __name__ == "__main__":
    
    fn_syntax = FNSyntax("2019-03-18_",
                         Var("Mode", str), "_",
                         Var("Wavelength", float), "nm,",
                         Var("ExpTime"), "ms,",
                         Var("Power", float), "uW.txt")
    
    fg = FileGroup.from_directory(path="D:\\! Nube\\Google Drive\\Proyecto OCT\\2019-02-05_Calibracion_espectrometro\\2019-03-18_Calibracion_CW\\prueba\\",
                                  fn_syntax=fn_syntax)
    
    def callback(self, path, mode, wavelength, exptime, power):
        return path, mode, wavelength, exptime, power
    
    output_vars = VarGroup(Var("Path", str),
                           Var("Mode", str),
                           Var("Wavelength", float),
                           Var("ExpTime", float),
                           Var("Power", float))
    
    bt = BatchTask(fg, None, callback,
                   (Var("Path", str), Var("Mode", str), Var("Wavelength", float), Var("ExpTime", float), Var("Power", float)),
                   PATH(),
                   FN_VAR("Mode"),
                   wavelength=FN_VAR("Wavelength"),
                   exptime=FN_VAR("ExpTime"),
                   power=FN_VAR("Power"))
    bt.run()
    
    print(bt.output_vars)




