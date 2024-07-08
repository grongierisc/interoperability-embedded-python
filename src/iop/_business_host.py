import datetime
import pickle
import codecs
import uuid
import decimal
import base64
import json
import importlib
import iris

from functools import wraps

from inspect import signature, getsource

from dacite import from_dict, Config

from iop._common import _Common
from iop._utils import _Utils

class _BusinessHost(_Common):
    """ This is a superclass for BusinessService, BusinesProcess, and BusinessOperation that
    defines common methods. It is a subclass of Common.
    """

    buffer:int = 64000
    DISPATCH = []

    def input_serialzer(fonction):
        """
        It takes a function as an argument, and returns a function that takes the same arguments as the
        original function, but serializes the arguments before passing them to the original function
        
        :param fonction: the function that will be decorated
        :return: The function dispatch_serializer is being returned.
        """
        def dispatch_serializer(self,*params, **param2):
            # Handle positional arguments
            serialized=[]
            for param in params:
                serialized.append(self._dispatch_serializer(param))
            # Handle keyword arguments
            for key, value in param2.items():
                param2[key] = self._dispatch_serializer(value)
            return fonction(self,*serialized, **param2)
        return dispatch_serializer
    
    def input_serialzer_param(position:int,name:str):
        """
        It takes a function as an argument, and returns a function that takes the same arguments as the
        original function, but serializes the arguments before passing them to the original function
        
        :param fonction: the function that will be decorated
        :return: The function dispatch_serializer is being returned.
        """
        def input_serialzer_param(fonction):
            @wraps(fonction)
            def dispatch_serializer(self,*params, **param2):
                # Handle positional arguments
                serialized=[]
                for i,param in enumerate(params):
                    if i == position:
                        serialized.append(self._dispatch_serializer(param))
                    else:
                        serialized.append(param)
                # Handle keyword arguments
                for key, value in param2.items():
                    if key == name:
                        param2[key] = self._dispatch_serializer(value)
                return fonction(self,*serialized, **param2)
            return dispatch_serializer
        return input_serialzer_param

    def output_deserialzer(fonction):
        """
        It takes a function as an argument, and returns a function that takes the same arguments as the
        original function, but returns the result of the original function passed to the
        `_dispatch_deserializer` function
        
        :param fonction: the function that will be decorated
        :return: The function dispatch_deserializer is being returned.
        """
        def dispatch_deserializer(self,*params, **param2):
            return self._dispatch_deserializer(fonction(self,*params, **param2))
            
        return dispatch_deserializer

    def input_deserialzer(fonction):
        """
        It takes a function as input, and returns a function that takes the same arguments as the input
        function, but deserializes the arguments before passing them to the input function
        
        :param fonction: the function that will be decorated
        :return: The function dispatch_deserializer is being returned.
        """
        def dispatch_deserializer(self,*params, **param2):
            # Handle positional arguments
            serialized=[]
            for param in params:
                serialized.append(self._dispatch_deserializer(param))
            # Handle keyword arguments
            for key, value in param2.items():
                param2[key] = self._dispatch_deserializer(value)
            return fonction(self,*serialized, **param2)
        return dispatch_deserializer

    def output_serialzer(fonction):
        """
        It takes a function as an argument, and returns a function that takes the same arguments as the
        original function, and returns the result of the original function, after passing it through the
        _dispatch_serializer function
        
        :param fonction: The function that is being decorated
        :return: The function dispatch_serializer is being returned.
        """
        def dispatch_serializer(self,*params, **param2):
            return self._dispatch_serializer(fonction(self,*params, **param2))
        return dispatch_serializer

    @input_serialzer_param(1,'request')
    @output_deserialzer
    def send_request_sync(self, target, request, timeout=-1, description=None):
        """ Send the specified message to the target business process or business operation synchronously.
            
        Parameters:
        target: a string that specifies the name of the business process or operation to receive the request. 
            The target is the name of the component as specified in the Item Name property in the production definition, not the class name of the component.
        request: specifies the message to send to the target. The request is either an instance of a class that is a subclass of Message class or of IRISObject class.
            If the target is a build-in ObjectScript component, you should use the IRISObject class. The IRISObject class enables the PEX framework to convert the message to a class supported by the target.
        timeout: an optional integer that specifies the number of seconds to wait before treating the send request as a failure. The default value is -1, which means wait forever.
        description: an optional string parameter that sets a description property in the message header. The default is None.
        Returns:
            the response object from target.
        Raises:
        TypeError: if request is not of type Message or IRISObject.
        """

        return self.iris_handle.dispatchSendRequestSync(target,request,timeout,description)

    @input_serialzer_param(1,'request')
    def send_request_async(self, target, request, description=None):
        """ Send the specified message to the target business process or business operation asynchronously.
        Parameters:
        target: a string that specifies the name of the business process or operation to receive the request. 
            The target is the name of the component as specified in the Item Name property in the production definition, not the class name of the component.
        request: specifies the message to send to the target. The request is an instance of IRISObject or of a subclass of Message.
            If the target is a built-in ObjectScript component, you should use the IRISObject class. The IRISObject class enables the PEX framework to convert the message to a class supported by the target.
        description: an optional string parameter that sets a description property in the message header. The default is None.
        
        Raises:
        TypeError: if request is not of type Message or IRISObject.
        """
        
        return self.iris_handle.dispatchSendRequestAsync(target,request,description)

    def _serialize_pickle_message(self,message):
        """ Converts a python dataclass message into an iris iop.message.

        Parameters:
        message: The message to serialize, an instance of a class that is a subclass of Message.

        Returns:
        string: The message in json format.
        """

        pickle_string = codecs.encode(pickle.dumps(message), "base64").decode()
        module = message.__class__.__module__
        classname = message.__class__.__name__

        msg = iris.cls('IOP.PickleMessage')._New()
        msg.classname = module + "." + classname

        stream = _Utils.string_to_stream(pickle_string)
        msg.jstr = stream

        return msg


    def _dispatch_serializer(self,message):
        """
        If the message is a message instance, serialize it as a message, otherwise, if it's a pickle message
        instance, serialize it as a pickle message, otherwise, return the message
        
        :param message: The message to be serialized
        :return: The serialized message
        """
        if (message is not None and self._is_message_instance(message)):
            return self._serialize_message(message)
        elif (message is not None and self._is_pickle_message_instance(message)):
            return self._serialize_pickle_message(message)
        elif (message is not None and self._is_iris_object_instance(message)):
            return message
        elif (message is None or message == ""):
            return message
        else:
            # todo : decorator takes care of all the parameters, so this should never happen
            # return message
            raise TypeError("The message must be an instance of a class that is a subclass of Message or IRISObject %Persistent class.")

    def _serialize_message(self,message):
        """ Converts a python dataclass message into an iris iop.message.

        Parameters:
        message: The message to serialize, an instance of a class that is a subclass of Message.

        Returns:
        string: The message in json format.
        """
        json_string = json.dumps(message, cls=IrisJSONEncoder, ensure_ascii=False)
        module = message.__class__.__module__
        classname = message.__class__.__name__

        msg = iris.cls('IOP.Message')._New()
        msg.classname = module + "." + classname

        stream = _Utils.string_to_stream(json_string)
        msg.jstr = stream

        return msg

    def _deserialize_pickle_message(self,serial):
        """ 
        Converts an iris iop.message into an python dataclass message.
        
        """
        string = _Utils.stream_to_string(serial.jstr)

        msg = pickle.loads(codecs.decode(string.encode(), "base64"))
        return msg

    def _dispatch_deserializer(self,serial):
        """
        If the serialized object is a Message, deserialize it as a Message, otherwise deserialize it as a
        PickleMessage
        
        :param serial: The serialized object
        :return: The return value is a tuple of the form (serial, serial_type)
        """
        if (serial is not None and type(serial).__module__.find('iris') == 0) and serial._IsA("IOP.Message"):
            return self._deserialize_message(serial)
        elif (serial is not None and type(serial).__module__.find('iris') == 0) and serial._IsA("IOP.PickleMessage"):
            return self._deserialize_pickle_message(serial)
        else:
            return serial

    def _deserialize_message(self,serial):
        """ 
        Converts an iris iop.message into an python dataclass message.
        """

        if (serial.classname is None):
            raise ValueError("JSON message malformed, must include classname")
        classname = serial.classname

        j = classname.rindex(".")
        if (j <=0):
            raise ValueError("Classname must include a module: " + classname)
        try:
            module = importlib.import_module(classname[:j])
            msg = getattr(module, classname[j+1:])
        except Exception:
            raise ImportError("Class not found: " + classname)

        string = _Utils.stream_to_string(serial.jstr)

        jdict = json.loads(string, cls=IrisJSONDecoder)
        msg = self._dataclass_from_dict(msg,jdict)
        return msg

    def _dataclass_from_dict(self,klass, dikt):
        """
        > If the field is not in the dataclass, then add it as an attribute
        
        :param klass: The dataclass to convert to
        :param dikt: the dictionary to convert to a dataclass
        :return: A dataclass object with the fields of the dataclass and the fields of the dictionary.
        """
        ret = from_dict(klass, dikt, Config(check_types=False))
        
        try:
            fieldtypes = klass.__annotations__
        except Exception as e:
            fieldtypes = []
        
        for key,val in dikt.items():
            if key not in fieldtypes:
                setattr(ret, key, val)
        return ret

    def _dispach_message(self, request):
        """
        It takes a request object, and returns a response object
        
        :param request: The request object
        :return: The return value is the result of the method call.
        """

        call = 'on_message'

        module = request.__class__.__module__
        classname = request.__class__.__name__

        for msg,method in self.DISPATCH:
            if msg == module+"."+classname:
                call = method

        return getattr(self,call)(request)

    
    def _create_dispatch(self):
        """
        It creates a list of tuples, where each tuple contains the name of a class and the name of a method
        that takes an instance of that class as its only argument
        :return: A list of tuples.
        """
        if len(self.DISPATCH) == 0:
            #get all function in current BO
            method_list = [func for func in dir(self) if callable(getattr(self, func)) and not func.startswith("_")]
            for method in method_list:
                #get signature of current function
                try:
                    param = signature(getattr(self, method)).parameters
                # Handle staticmethod
                except ValueError as e:
                    param=''
                #one parameter
                if (len(param)==1):
                    #get parameter type
                    annotation = str(param[list(param)[0]].annotation)
                    #trim annotation format <class 'toto'>
                    i = annotation.find("'")
                    j = annotation.rfind("'")
                    #if end is not found
                    if j == -1:
                        j = None
                    classname = annotation[i+1:j]
                    self.DISPATCH.append((classname,method))
        return

    @staticmethod
    def OnGetConnections():
        """ The OnGetConnections() method returns all of the targets of any SendRequestSync or SendRequestAsync
        calls for the class. Implement this method to allow connections between components to show up in 
        the interoperability UI.

        Returns:
            An IRISList containing all targets for this class. Default is None.
        """
        return None

    def SendRequestSync(self, target, request, timeout=-1, description=None):
        """ DEPRECATED : use send_request_sync
        `SendRequestSync` is a function that sends a request to a target and waits for a response
        
        :param target: The target of the request
        :param request: The request to send
        :param timeout: The timeout in seconds. If the timeout is negative, the default timeout will be used
        :param description: A string that describes the request. This is used for logging purposes
        :return: The return value is a tuple of (response, status).
        """
        return self.send_request_sync(target,request,timeout,description)
        
    def SendRequestAsync(self, target, request, description=None):
        """ DEPRECATED : use send_request_async
        It takes a target, a request, and a description, and returns a send_request_async function
        
        :param target: The target of the request. This is the name of the function you want to call
        :param request: The request to send
        :param description: A string that describes the request
        :return: The return value is a Future object.
        """
        return self.send_request_async(target,request,description)

    @staticmethod
    def getAdapterType():
        """ DEPRECATED : use get_adapter_type
        Name of the registred Adapter
        """
        return
        
    @staticmethod
    def get_adapter_type():
        """
        Name of the registred Adapter
        """
        return 
    
    def on_get_connections(self) -> list:
        """
        The OnGetConnections() method returns all of the targets of any SendRequestSync or SendRequestAsync
        calls for the class. Implement this method to allow connections between components to show up in 
        the interoperability UI.

        Returns:
            An IRISList containing all targets for this class. Default is None.
        """
        ## Parse the class code to find all invocations of send_request_sync and send_request_async
        ## and return the targets
        targer_list = []
        # get the source code of the class
        source = getsource(self.__class__)
        # find all invocations of send_request_sync and send_request_async
        for method in ['send_request_sync','send_request_async','SendRequestSync','SendRequestAsync']:
            i = source.find(method)
            while i != -1:
                j = source.find("(",i)
                if j != -1:
                    k = source.find(",",j)
                    if k != -1:
                        target = source[j+1:k]
                        if target.find("=") != -1:
                            # it's a keyword argument, remove the keyword
                            target = target[target.find("=")+1:].strip()
                        if target not in targer_list:
                            targer_list.append(target)
                i = source.find(method,i+1)

        for target in targer_list:
            # if target is a string, remove the quotes
            if target[0] == "'" and target[-1] == "'":
                targer_list[targer_list.index(target)] = target[1:-1]
            elif target[0] == '"' and target[-1] == '"':
                targer_list[targer_list.index(target)] = target[1:-1]
            # if target is a variable, try to find the value of the variable
            else:
                self.on_init()
                try:
                    if target.find("self.") != -1:
                        # it's a class variable
                        targer_list[targer_list.index(target)] = getattr(self,target[target.find(".")+1:])
                    elif target.find(".") != -1:
                        # it's a class variable
                        targer_list[targer_list.index(target)] = getattr(getattr(self,target[:target.find(".")]),target[target.find(".")+1:])
                    else:
                        targer_list[targer_list.index(target)] = getattr(self,target)
                except Exception as e:
                    pass

        return targer_list

# It's a subclass of the standard JSONEncoder class that knows how to encode date/time, decimal types,
# and UUIDs.
class IrisJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    """

    def default(self, o):
        if o.__class__.__name__ == 'DataFrame':
            return 'dataframe:'+o.to_json(orient="table")
        elif isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r[:-6] + "Z"
            return 'datetime:'+r
        elif isinstance(o, datetime.date):
            return 'date:'+o.isoformat()
        elif isinstance(o, datetime.time):
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return 'time:'+r
        elif isinstance(o, decimal.Decimal): 
            return 'decimal:'+str(o)
        elif isinstance(o, uuid.UUID):
            return 'uuid:'+str(o)
        elif isinstance(o, bytes):
            return 'bytes:'+base64.b64encode(o).decode("UTF-8")
        elif hasattr(o, '__dict__'):
            return o.__dict__
        else:
            return super().default(o)

# It's a JSON decoder that looks for a colon in the value of a key/value pair. If it finds one, it
# assumes the value is a string that represents a type and a value. It then converts the value to the
# appropriate type
class IrisJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        ret = {}
        for key, value in obj.items():
            i = 0
            if isinstance(value, str):
                i = value.find(":") 
            if (i>0):
                typ = value[:i]
                if typ == 'datetime':
                    ret[key] = datetime.datetime.fromisoformat(value[i+1:])
                elif typ == 'date':
                    ret[key] = datetime.date.fromisoformat(value[i+1:])
                elif typ == 'time':
                    ret[key] = datetime.time.fromisoformat(value[i+1:])
                elif typ == 'dataframe':
                    module = importlib.import_module('pandas')
                    ret[key] = module.read_json(value[i+1:],orient="table")
                elif typ == 'decimal':
                    ret[key] = decimal.Decimal(value[i+1:])
                elif typ == 'uuid':
                    ret[key] = uuid.UUID(value[i+1:])
                elif typ == 'bytes':
                    ret[key] = base64.b64decode((value[i+1:].encode("UTF-8")))
                else:
                    ret[key] = value
            else:
                ret[key] = value
        return ret
