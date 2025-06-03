import os
import sys
import importlib
import importlib.util
import importlib.resources
import json
import inspect
import ast
from typing import Any, Dict, Optional, Union, Tuple

import xmltodict
from pydantic import TypeAdapter

from . import _iris
from ._message import _Message, _PydanticMessage

class _Utils():
    @staticmethod
    def raise_on_error(sc):
        """
        If the status code is an error, raise an exception
        
        :param sc: The status code returned by the Iris API
        """
        if _iris.get_iris().system.Status.IsError(sc):
            raise RuntimeError(_iris.get_iris().system.Status.GetOneStatusText(sc))

    @staticmethod
    def setup(path:Optional[str] = None):

        if path is None:
            # get the path of the data folder with importlib.resources
            try:
                path = str(importlib.resources.files('iop').joinpath('cls'))
            except ModuleNotFoundError:
                path = None

        if path:
            _Utils.raise_on_error(_iris.get_iris().cls('%SYSTEM.OBJ').LoadDir(path,'cubk',"*.cls",1))

        # for retrocompatibility load grongier.pex
        try:
            path = str(importlib.resources.files('grongier').joinpath('cls'))
        except ModuleNotFoundError:
            path = None

        if path:
            _Utils.raise_on_error(_iris.get_iris().cls('%SYSTEM.OBJ').LoadDir(path,'cubk',"*.cls",1))

    @staticmethod
    def register_message_schema(msg_cls: type):
        """
        It takes a class and registers the schema
        
        :param cls: The class to register
        """
        if issubclass(msg_cls,_PydanticMessage):
            schema = msg_cls.model_json_schema()
        elif issubclass(msg_cls,_Message):
            type_adapter = TypeAdapter(msg_cls)
            schema = type_adapter.json_schema()
        else:
            raise ValueError("The class must be a subclass of _Message or _PydanticMessage")
        schema_name = msg_cls.__module__ + '.' + msg_cls.__name__
        schema_str = json.dumps(schema)
        categories = schema_name
        _Utils.register_schema(schema_name,schema_str,categories)

    @staticmethod
    def register_schema(schema_name:str, schema_str:str,categories:str):
        """
        It takes a schema name, a schema string, and a category string, and registers the schema
        
        :param schema_name: The name of the schema
        :type schema_name: str
        :param schema_str: The schema as a string
        :type schema_str: str
        :param categories: The categories of the schema
        :type categories: str
        """
        _Utils.raise_on_error(_iris.get_iris().cls('IOP.Message.JSONSchema').Import(schema_str,categories,schema_name))

    @staticmethod
    def get_python_settings() -> Tuple[str,str,str]:
        import iris_utils._cli

        pythonlib = iris_utils._cli.find_libpython()
        pythonpath = _Utils._get_python_path()
        pythonversion = sys.version[:4]

        if not pythonlib:
            pythonlib = ""
            
        return pythonlib, pythonpath, pythonversion

    @staticmethod
    def _get_python_path() -> str:

        if "VIRTUAL_ENV" in os.environ:
            return os.path.join(
                os.environ["VIRTUAL_ENV"],
                "lib", 
                f"python{sys.version[:4]}", 
                "site-packages"
            )
        return ""

    @staticmethod
    def register_component(module:str,classname:str,path:str,overwrite:int=1,iris_classname:str='Python'):
        """
        It registers a component in the Iris database.
        
        :param module: The name of the module that contains the class
        :type module: str
        :param classname: The name of the class you want to register
        :type classname: str
        :param path: The path to the component
        :type path: str
        :param overwrite: 0 = no, 1 = yes
        :type overwrite: int
        :param iris_classname: The name of the class in the Iris class hierarchy
        :type iris_classname: str
        :return: The return value is a string.
        """
        path = os.path.abspath(os.path.normpath(path))
        fullpath = _Utils.guess_path(module,path)
        pythonlib, pythonpath, pythonversion = _Utils.get_python_settings()
        try:
            _iris.get_iris().cls('IOP.Utils').dispatchRegisterComponent(module,classname,path,fullpath,overwrite,iris_classname,pythonlib,pythonpath,pythonversion)
        except RuntimeError as e:
            # New message error : Make sure the iop package is installed in iris 
            raise RuntimeError("Iris class : IOP.Utils not found. Make sure the iop package is installed in iris eg: iop --init.") from e

    @staticmethod
    def register_folder(path:str,overwrite:int=1,iris_package_name:str='Python'):
        """
        > This function takes a path to a folder, and registers all the Python files in that folder as IRIS
        classes
        
        :param path: the path to the folder containing the files you want to register
        :type path: str
        :param overwrite: 
        :type overwrite: int
        :param iris_package_name: The name of the iris package you want to register the file to
        :type iris_package_name: str
        """
        path = os.path.normpath(path)
        # get the absolute path of the folder
        path = os.path.abspath(path)
        for filename in os.listdir(path):
            if filename.endswith(".py"): 
                _Utils._register_file(filename, path, overwrite, iris_package_name)
            else:
                continue

    @staticmethod
    def register_file(file:str,overwrite:int=1,iris_package_name:str='Python'):
        """
        It takes a file name, a boolean to overwrite existing components, and the name of the Iris
        package that the file is in. It then opens the file, parses it, and looks for classes that extend
        BusinessOperation, BusinessProcess, or BusinessService. If it finds one, it calls register_component
        with the module name, class name, path, overwrite boolean, and the full Iris package name
        
        :param file: the name of the file containing the component
        :type file: str
        :param overwrite: if the component already exists, overwrite it
        :type overwrite: int
        :param iris_package_name: the name of the iris package that you want to register the components to
        :type iris_package_name: str
        """
        head_tail = os.path.split(file)
        return _Utils._register_file(head_tail[1],head_tail[0],overwrite,iris_package_name)

    @staticmethod
    def _register_file(filename:str,path:str,overwrite:int=1,iris_package_name:str='Python'):
        """
        It takes a file name, a path, a boolean to overwrite existing components, and the name of the Iris
        package that the file is in. It then opens the file, parses it, and looks for classes that extend
        BusinessOperation, BusinessProcess, or BusinessService. If it finds one, it calls register_component
        with the module name, class name, path, overwrite boolean, and the full Iris package name
        
        :param filename: the name of the file containing the component
        :type filename: str
        :param path: the path to the directory containing the files to be registered
        :type path: str
        :param overwrite: if the component already exists, overwrite it
        :type overwrite: int
        :param iris_package_name: the name of the iris package that you want to register the components to
        :type iris_package_name: str
        """
        #pour chaque classe dans le module, appeler register_component
        f =  os.path.join(path,filename)
        with open(f) as file:
            node = ast.parse(file.read())
            #list of class in the file
            classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
            for klass in classes:
                extend = ''
                if len(klass.bases) == 1:
                    base = klass.bases[0]
                    if isinstance(base, ast.Name):
                        extend = base.id
                    elif isinstance(base, ast.Attribute):
                        extend = base.attr
                if extend in ('BusinessOperation','BusinessProcess','BusinessService','DuplexService','DuplexProcess','DuplexOperation','InboundAdapter','OutboundAdapter'):
                    module = _Utils.filename_to_module(filename)
                    iris_class_name = f"{iris_package_name}.{module}.{klass.name}"
                    # strip "_" for iris class name
                    iris_class_name = iris_class_name.replace('_','')
                    _Utils.register_component(module, klass.name, path, overwrite, iris_class_name)
    @staticmethod
    def register_package(package:str,path:str,overwrite:int=1,iris_package_name:str='Python'):
        """
        It takes a package name, a path to the package, a flag to overwrite existing files, and the name of
        the iris package to register the files to. It then loops through all the files in the package and
        registers them to the iris package
        
        :param package: the name of the package you want to register
        :type package: str
        :param path: the path to the directory containing the package
        :type path: str
        :param overwrite: 0 = don't overwrite, 1 = overwrite
        :type overwrite: int
        :param iris_package_name: The name of the package in the Iris package manager
        :type iris_package_name: str
        """
        for filename in os.listdir(os.path.join(path,package)):
            if filename.endswith(".py"):
                _Utils._register_file(filename, os.path.join(path,package), overwrite, iris_package_name)
            else:
                continue

    @staticmethod
    def filename_to_module(filename) -> str:
        """
        It takes a filename and returns the module name
        
        :param filename: The name of the file to be imported
        :return: The module name
        """
        module = ''

        path,file = os.path.split(filename)
        mod = file.split('.')[0]
        packages = path.replace(os.sep, ('.'))
        if len(packages) >1:
            module = packages+'.'+mod
        else:
            module = mod

        return module

    @staticmethod
    def migrate(filename=None):
        """ 
        Read the settings.py file and register all the components
        settings.py file has two dictionaries:
            * CLASSES
                * key: the name of the class
                * value: an instance of the class
            * PRODUCTIONS
                list of dictionaries:
                * key: the name of the production
                * value: a dictionary containing the settings for the production
            * SCHEMAS
                List of classes
        """
        path = None
        # try to load the settings file
        if filename:
            # check if the filename is absolute or relative
            if os.path.isabs(filename):
                path = os.path.dirname(filename)
            else:
                raise ValueError("The filename must be absolute")
            # add the path to the system path to the beginning
            sys.path.insert(0,os.path.normpath(path))
            # import settings from the specified file
            settings = _Utils.import_module_from_path('settings',filename)
        else:
            # import settings from the settings module
            import settings # type: ignore
        # get the path of the settings file
        path = os.path.dirname(inspect.getfile(settings))
        try:
            # set the classes settings
            _Utils.set_classes_settings(settings.CLASSES,path)
        except AttributeError:
            print("No classes to register")
        try:
            # set the productions settings
            _Utils.set_productions_settings(settings.PRODUCTIONS,path)
        except AttributeError:
            print("No productions to register")
        try:
            # set the schemas
            for cls in settings.SCHEMAS:
                _Utils.register_message_schema(cls)
        except AttributeError:
            print("No schemas to register")
        try:
            sys.path.remove(os.path.normpath(path))
        except ValueError:
            pass

    @staticmethod
    def import_module_from_path(module_name, file_path):
        if not os.path.isabs(file_path):
            raise ValueError("The file path must be absolute")
        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot find module named {module_name} at {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def set_classes_settings(class_items,root_path=None):
        """
        It takes a dictionary of classes and returns a dictionary of settings for each class
        
        :param class_items: a dictionary of classes
        :return: a dictionary of settings for each class
        """
        for key, value in class_items.items():
            if inspect.isclass(value):
                path = None
                if root_path:
                    path = root_path
                else:
                    path = os.path.dirname(inspect.getfile(value))
                _Utils.register_component(value.__module__,value.__name__,path,1,key)
            elif inspect.ismodule(value):
                path = None
                if root_path:
                    path = root_path
                else:
                    path = os.path.dirname(inspect.getfile(value))
                _Utils._register_file(value.__name__+'.py',path,1,key)
            # if the value is a dict
            elif isinstance(value,dict):
                # if the dict has a key 'path' and a key 'module' and a key 'class'
                if 'path' in value and 'module' in value and 'class' in value:
                    # register the component
                    _Utils.register_component(value['module'],value['class'],value['path'],1,key)
                # if the dict has a key 'path' and a key 'package'
                elif 'path' in value and 'package' in value:
                    # register the package
                    _Utils.register_package(value['package'],value['path'],1,key)
                # if the dict has a key 'path' and a key 'file'
                elif 'path' in value and 'file' in value:
                    # register the file
                    _Utils._register_file(value['file'],value['path'],1,key)
                # if the dict has a key 'path'
                elif 'path' in value:
                    # register folder
                    _Utils.register_folder(value['path'],1,key)
                else:
                    raise ValueError(f"Invalid value for {key}.")

    @staticmethod
    def set_productions_settings(production_list,root_path=None):
        """
        It takes a list of dictionaries and registers the productions
        """
        # for each production in the list
        for production in production_list:
            # get the production name (first key in the dictionary)
            production_name = list(production.keys())[0]
            # set the first key to 'production'
            production['Production'] = production.pop(production_name)
            # handle Items
            production = _Utils.handle_items(production,root_path)
            # transform the json as an xml
            xml = _Utils.dict_to_xml(production)
            # register the production
            _Utils.register_production(production_name,xml)

    @staticmethod
    def handle_items(production,root_path=None):
        # if an item is a class, register it and replace it with the name of the class
        if 'Item' in production['Production']:
            # for each item in the list
            for i,item in enumerate(production['Production']['Item']):
                # if the attribute "@ClassName" is a class, register it and replace it with the name of the class
                if '@ClassName' in item:
                    if inspect.isclass(item['@ClassName']):
                        path = None
                        if root_path:
                            path = root_path
                        else:
                            path = os.path.dirname(inspect.getfile(item['@ClassName']))
                        _Utils.register_component(item['@ClassName'].__module__,item['@ClassName'].__name__,path,1,item['@Name'])
                        # replace the class with the name of the class
                        production['Production']['Item'][i]['@ClassName'] = item['@Name']
                # if the attribute "@ClassName" is a dict
                elif isinstance(item['@ClassName'],dict):
                    # create a new dict where the key is the name of the class and the value is the dict
                    class_dict = {item['@Name']:item['@ClassName']}
                    # pass the new dict to set_classes_settings
                    _Utils.set_classes_settings(class_dict)
                    # replace the class with the name of the class
                    production['Production']['Item'][i]['@ClassName'] = item['@Name']
                else:
                    raise ValueError(f"Invalid value for {item['@Name']}.")

        return production

    @staticmethod
    def dict_to_xml(json):
        """
        It takes a json and returns an xml
        
        :param json: a json
        :return: an xml
        """
        xml = xmltodict.unparse(json,pretty=True)
        # remove the xml version tag
        xml = xml.replace('<?xml version="1.0" encoding="utf-8"?>','')
        # remove the new line at the beginning of the xml
        xml = xml[1:]
        return xml
    
    @staticmethod
    def register_production(production_name,xml):
        """
        It takes a production name and an xml and registers the production
        
        :param production_name: the name of the production
        :type production_name: str
        :param xml: the xml of the production
        :type xml: str
        """
        # split the production name in the package name and the production name
        # the production name is the last part of the string
        package = '.'.join(production_name.split('.')[:-1])
        production_name = production_name.split('.')[-1]
        stream = _Utils.string_to_stream(xml)
        # register the production
        _Utils.raise_on_error(_iris.get_iris().cls('IOP.Utils').CreateProduction(package,production_name,stream))

    @staticmethod
    def export_production(production_name):
        """
        It takes a production name and exports the production
        
        :param production_name: the name of the production
        :type production_name: str
        """
        def postprocessor(path, key, value):
            if value is None:
                return key, ''
            return key, value
        # export the production
        xdata = _iris.get_iris().cls('IOP.Utils').ExportProduction(production_name)
        # for each chunk of 1024 characters
        string = _Utils.stream_to_string(xdata)
        # convert the xml to a dictionary
        data = xmltodict.parse(string,postprocessor=postprocessor)
        # return the dictionary
        return data

    @staticmethod
    def stream_to_string(stream,buffer=1000000)-> str:
        string = ""
        stream.Rewind()
        while not stream.AtEnd:
            string += stream.Read(buffer)
        return string
    
    @staticmethod
    def string_to_stream(string:str,buffer=1000000):
        stream = _iris.get_iris().cls('%Stream.GlobalCharacter')._New()
        n = buffer
        chunks = [string[i:i+n] for i in range(0, len(string), n)]
        for chunk in chunks:
            stream.Write(chunk)
        return stream
    
    @staticmethod
    def guess_path(module: str, path: str) -> str:
        """Determines the full file path for a given module.
        
        Args:
            module: Module name/path (e.g. 'foo.bar' or '.foo.bar')
            path: Base directory path
            
        Returns:
            Full path to the module's .py file
        """
        if not module:
            raise ValueError("Module name cannot be empty")
            
        if module.startswith("."):
            # Handle relative imports
            dot_count = len(module) - len(module.lstrip("."))
            module = module[dot_count:]
            
            # Go up directory tree based on dot count
            for _ in range(dot_count - 1):
                path = os.path.dirname(path)
                
        # Convert module path to file path
        if module.endswith(".py"):
            module_path = module.replace(".", os.sep)
        else:
            module_path = module.replace(".", os.sep) + ".py"
        return os.path.join(path, module_path)