import abc
import asyncio
import base64
import codecs
import datetime
import decimal
import importlib
import inspect
import iris
import json
import pickle
import uuid
from dataclasses import dataclass
from functools import wraps
from inspect import getsource, signature
from typing import Any, Callable, ClassVar, Dict, List, Optional, Tuple, Type, Union

from dacite import Config, from_dict

from iop._common import _Common
from iop._message import _Message as Message
from iop._utils import _Utils

class _BusinessHost(_Common):
    """Base class for business components that defines common methods.
    
    This is a superclass for BusinessService, BusinessProcess, and BusinessOperation that
    defines common functionality like message serialization/deserialization and request handling.
    """

    buffer: int = 64000
    DISPATCH: List[Tuple[str, str]] = []

    def input_serialzer(fonction: Callable) -> Callable:
        """Decorator that serializes input arguments before passing to function.
        
        Args:
            fonction: Function to decorate
            
        Returns:
            Decorated function that handles serialization
        """
        def dispatch_serializer(self, *params: Any, **param2: Any) -> Any:
            # Handle positional arguments using list comprehension
            serialized = [self._dispatch_serializer(param) for param in params]
            
            # Handle keyword arguments using dictionary comprehension
            param2 = {key: self._dispatch_serializer(value) for key, value in param2.items()}
            
            return fonction(self, *serialized, **param2)
        return dispatch_serializer
    
    def input_serialzer_param(position: int, name: str) -> Callable:
        """Decorator that serializes specific parameter by position or name.
        
        Args:
            position: Position of parameter to serialize
            name: Name of parameter to serialize
            
        Returns:
            Decorator function
        """
        def input_serialzer_param(fonction: Callable) -> Callable:
            @wraps(fonction)
            def dispatch_serializer(self, *params: Any, **param2: Any) -> Any:
                # Handle positional arguments using list comprehension
                serialized = [
                    self._dispatch_serializer(param) if i == position else param
                    for i, param in enumerate(params)
                ]
                
                # Handle keyword arguments using dictionary comprehension
                param2 = {
                    key: self._dispatch_serializer(value) if key == name else value
                    for key, value in param2.items()
                }
                
                return fonction(self, *serialized, **param2)
            return dispatch_serializer
        return input_serialzer_param

    def output_deserialzer(fonction: Callable) -> Callable:
        """Decorator that deserializes output of function.
        
        Args:
            fonction: Function to decorate
            
        Returns:
            Decorated function that handles deserialization
        """
        def dispatch_deserializer(self, *params: Any, **param2: Any) -> Any:
            return self._dispatch_deserializer(fonction(self, *params, **param2))
            
        return dispatch_deserializer

    def input_deserialzer(fonction: Callable) -> Callable:
        """Decorator that deserializes input arguments before passing to function.
        
        Args:
            fonction: Function to decorate
            
        Returns:
            Decorated function that handles deserialization
        """
        def dispatch_deserializer(self, *params: Any, **param2: Any) -> Any:
            # Handle positional arguments using list comprehension
            serialized = [self._dispatch_deserializer(param) for param in params]
            
            # Handle keyword arguments using dictionary comprehension
            param2 = {key: self._dispatch_deserializer(value) for key, value in param2.items()}
            
            return fonction(self, *serialized, **param2)
        return dispatch_deserializer

    def output_serialzer(fonction: Callable) -> Callable:
        """Decorator that serializes output of function.
        
        Args:
            fonction: Function to decorate
            
        Returns:
            Decorated function that handles serialization
        """
        def dispatch_serializer(self, *params: Any, **param2: Any) -> Any:
            return self._dispatch_serializer(fonction(self, *params, **param2))
        return dispatch_serializer

    @input_serialzer_param(1, 'request')
    @output_deserialzer
    def send_request_sync(self, target: str, request: Union[Message, Any], 
                         timeout: int = -1, description: Optional[str] = None) -> Any:
        """Send message synchronously to target component.
        
        Args:
            target: Name of target component
            request: Message to send
            timeout: Timeout in seconds, -1 means wait forever 
            description: Optional description for logging
            
        Returns:
            Response from target component
            
        Raises:
            TypeError: If request is invalid type
        """
        return self.iris_handle.dispatchSendRequestSync(target, request, timeout, description)

    @input_serialzer_param(1, 'request')
    def send_request_async(self, target: str, request: Union[Message, Any], 
                          description: Optional[str] = None) -> None:
        """Send message asynchronously to target component.
        
        Args:
            target: Name of target component
            request: Message to send
            description: Optional description for logging
            
        Raises:
            TypeError: If request is invalid type
        """
        return self.iris_handle.dispatchSendRequestAsync(target, request, description)
    
    async def send_request_async_ng(self, target: str, request: Union[Message, Any], 
                                   timeout: int = -1, description: Optional[str] = None) -> Any:
        """Send message asynchronously to target component with asyncio.
        
        Args:
            target: Name of target component
            request: Message to send
            timeout: Timeout in seconds, -1 means wait forever 
            description: Optional description for logging
            
        Returns:
            Response from target component
        """
        return await _send_request_async_ng(target, request, timeout, description, self)

    def send_multi_request_sync(self, target_request: List[Tuple[str, Union[Message, Any]]], 
                                timeout: int = -1, description: Optional[str] = None) -> List[Tuple[str, Union[Message, Any], Any, int]]:
        """Send multiple messages synchronously to target components.
        
        Args:
            target_request: List of tuples (target, request) to send
            timeout: Timeout in seconds, -1 means wait forever 
            description: Optional description for logging
            
        Returns:
            List of tuples (target, request, response, status)
        """
        # create a list of iris.Ens.CallStructure for each target_request
        call_list = []
        # sanity check
        if not isinstance(target_request, list):
            raise TypeError("The target_request parameter must be a list")
        if len(target_request) == 0:
            raise ValueError("The target_request parameter must not be empty")
        # check if the target_request is a list of tuple of 2 elements
        if not all(isinstance(item, tuple) and len(item) == 2 for item in target_request):
            raise TypeError("The target_request parameter must be a list of tuple of 2 elements")

        for target, request in target_request:
            call = iris.cls("Ens.CallStructure")._New()
            call.TargetDispatchName = target
            call.Request = self._dispatch_serializer(request)
            call_list.append(call)
        # call the dispatchSendMultiRequestSync method
        response_list = self.iris_handle.dispatchSendRequestSyncMultiple(call_list, timeout)
        # create a list of tuple (target, request, response, status)
        result = []
        for i in range(len(target_request)):
            result.append(
                (target_request[i][0],
                 target_request[i][1],
                 self._dispatch_deserializer(response_list[i].Response),
                 response_list[i].ResponseCode
                ))
        return result


    def _serialize_pickle_message(self, message: Any) -> iris.cls:
        """Converts a python dataclass message into an iris iop.message.

        Args:
            message: The message to serialize, an instance of a class that is a subclass of Message.

        Returns:
            The message in json format.
        """
        pickle_string = codecs.encode(pickle.dumps(message), "base64").decode()
        module = message.__class__.__module__
        classname = message.__class__.__name__

        msg = iris.cls('IOP.PickleMessage')._New()
        msg.classname = module + "." + classname

        stream = _Utils.string_to_stream(pickle_string)
        msg.jstr = stream

        return msg


    def _dispatch_serializer(self, message: Any) -> Any:
        """Serializes the message based on its type.
        
        Args:
            message: The message to serialize
            
        Returns:
            The serialized message
            
        Raises:
            TypeError: If message is invalid type
        """
        if message is not None:
            if self._is_message_instance(message):
                return self._serialize_message(message)
            elif self._is_pickle_message_instance(message):
                return self._serialize_pickle_message(message)
            elif self._is_iris_object_instance(message):
                return message

        if message == "" or message is None:
            return message

        # todo : decorator takes care of all the parameters, so this should never happen
        # return message
        raise TypeError("The message must be an instance of a class that is a subclass of Message or IRISObject %Persistent class.")

    def _serialize_message(self, message: Any) -> iris.cls:
        """Converts a python dataclass message into an iris iop.message.

        Args:
            message: The message to serialize, an instance of a class that is a subclass of Message.

        Returns:
            The message in json format.
        """
        json_string = json.dumps(message, cls=IrisJSONEncoder, ensure_ascii=False)
        module = message.__class__.__module__
        classname = message.__class__.__name__

        msg = iris.cls('IOP.Message')._New()
        msg.classname = module + "." + classname

        if hasattr(msg, 'buffer') and len(json_string) > msg.buffer:
            msg.json = _Utils.string_to_stream(json_string, msg.buffer)
        else:
            msg.json = json_string

        return msg

    def _deserialize_pickle_message(self, serial: iris.cls) -> Any:
        """Converts an iris iop.message into a python dataclass message.
        
        Args:
            serial: The serialized message
            
        Returns:
            The deserialized message
        """
        string = _Utils.stream_to_string(serial.jstr)

        msg = pickle.loads(codecs.decode(string.encode(), "base64"))
        return msg

    def _dispatch_deserializer(self, serial: Any) -> Any:
        """Deserializes the message based on its type.
        
        Args:
            serial: The serialized message
            
        Returns:
            The deserialized message
        """
        if (
            serial is not None
            and type(serial).__module__.startswith('iris')
            and (
                serial._IsA("IOP.Message")
                or serial._IsA("Grongier.PEX.Message")
            )
        ):
            return self._deserialize_message(serial)
        elif (
            serial is not None
            and type(serial).__module__.startswith('iris')
            and (
                serial._IsA("IOP.PickleMessage")
                or serial._IsA("Grongier.PEX.PickleMessage")
            )
        ):
            return self._deserialize_pickle_message(serial)
        else:
            return serial

    def _deserialize_message(self, serial: iris.cls) -> Any:
        """Converts an iris iop.message into a python dataclass message.
        
        Args:
            serial: The serialized message
            
        Returns:
            The deserialized message
        """
        if (serial.classname is None):
            raise ValueError("JSON message malformed, must include classname")
        classname = serial.classname

        j = classname.rindex(".")
        if (j <= 0):
            raise ValueError("Classname must include a module: " + classname)
        try:
            module = importlib.import_module(classname[:j])
            msg = getattr(module, classname[j+1:])
        except Exception:
            raise ImportError("Class not found: " + classname)

        string = ""
        if (serial.type == 'Stream'):
            string = _Utils.stream_to_string(serial.json)
        else:
            string = serial.json

        jdict = json.loads(string, cls=IrisJSONDecoder)
        msg = self._dataclass_from_dict(msg, jdict)
        return msg

    def _dataclass_from_dict(self, klass: Type, dikt: Dict) -> Any:
        """Converts a dictionary to a dataclass instance.
        
        Args:
            klass: The dataclass to convert to
            dikt: The dictionary to convert to a dataclass
            
        Returns:
            A dataclass object with the fields of the dataclass and the fields of the dictionary.
        """
        ret = from_dict(klass, dikt, Config(check_types=False))
        
        try:
            fieldtypes = klass.__annotations__
        except Exception as e:
            fieldtypes = []
        
        for key, val in dikt.items():
            if key not in fieldtypes:
                setattr(ret, key, val)
        return ret

    def _dispach_message(self, request: Any) -> Any:
        """Dispatches the message to the appropriate method.
        
        Args:
            request: The request object
            
        Returns:
            The response object
        """
        call = 'on_message'

        module = request.__class__.__module__
        classname = request.__class__.__name__

        for msg, method in self.DISPATCH:
            if msg == module + "." + classname:
                call = method

        return getattr(self, call)(request)

    
    def _create_dispatch(self) -> None:
        """Creates a list of tuples, where each tuple contains the name of a class and the name of a method
        that takes an instance of that class as its only argument.
        """
        if len(self.DISPATCH) == 0:
            # get all function in current BO
            method_list = [func for func in dir(self) if callable(getattr(self, func)) and not func.startswith("_")]
            for method in method_list:
                # get signature of current function
                try:
                    param = signature(getattr(self, method)).parameters
                # Handle staticmethod
                except ValueError as e:
                    param = ''
                # one parameter
                if (len(param) == 1):
                    # get parameter type
                    annotation = str(param[list(param)[0]].annotation)
                    # trim annotation format <class 'toto'>
                    i = annotation.find("'")
                    j = annotation.rfind("'")
                    # if end is not found
                    if j == -1:
                        j = None
                    classname = annotation[i+1:j]
                    self.DISPATCH.append((classname, method))
        return

    @staticmethod
    def OnGetConnections() -> Optional[List[str]]:
        """The OnGetConnections() method returns all of the targets of any SendRequestSync or SendRequestAsync
        calls for the class. Implement this method to allow connections between components to show up in 
        the interoperability UI.

        Returns:
            An IRISList containing all targets for this class. Default is None.
        """
        return None

    def SendRequestSync(self, target: str, request: Union[Message, Any], 
                       timeout: int = -1, description: Optional[str] = None) -> Any:
        """DEPRECATED: use send_request_sync.
        
        Args:
            target: The target of the request
            request: The request to send
            timeout: The timeout in seconds, -1 means wait forever 
            description: A string that describes the request
            
        Returns:
            The response from the target component
        """
        return self.send_request_sync(target, request, timeout, description)
        
    def SendRequestAsync(self, target: str, request: Union[Message, Any], 
                        description: Optional[str] = None) -> None:
        """DEPRECATED: use send_request_async.
        
        Args:
            target: The target of the request
            request: The request to send
            description: A string that describes the request
        """
        return self.send_request_async(target, request, description)

    @staticmethod
    def getAdapterType() -> Optional[str]:
        """DEPRECATED: use get_adapter_type.
        
        Returns:
            Name of the registered Adapter
        """
        return
        
    @staticmethod
    def get_adapter_type() -> Optional[str]:
        """Returns the name of the registered Adapter.
        
        Returns:
            Name of the registered Adapter
        """
        return 
    
    def on_get_connections(self) -> List[str]:
        """The OnGetConnections() method returns all of the targets of any SendRequestSync or SendRequestAsync
        calls for the class. Implement this method to allow connections between components to show up in 
        the interoperability UI.

        Returns:
            A list containing all targets for this class.
        """
        ## Parse the class code to find all invocations of send_request_sync and send_request_async
        ## and return the targets
        targer_list = []
        # get the source code of the class
        source = getsource(self.__class__)
        # find all invocations of send_request_sync and send_request_async
        for method in ['send_request_sync', 'send_request_async', 'SendRequestSync', 'SendRequestAsync']:
            i = source.find(method)
            while i != -1:
                j = source.find("(", i)
                if j != -1:
                    k = source.find(",", j)
                    if k != -1:
                        target = source[j+1:k]
                        if target.find("=") != -1:
                            # it's a keyword argument, remove the keyword
                            target = target[target.find("=")+1:].strip()
                        if target not in targer_list:
                            targer_list.append(target)
                i = source.find(method, i+1)

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
                        targer_list[targer_list.index(target)] = getattr(self, target[target.find(".")+1:])
                    elif target.find(".") != -1:
                        # it's a class variable
                        targer_list[targer_list.index(target)] = getattr(getattr(self, target[:target.find(".")]), target[target.find(".")+1:])
                    else:
                        targer_list[targer_list.index(target)] = getattr(self, target)
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

    def default(self, o: Any) -> Any:
        if o.__class__.__name__ == 'DataFrame':
            return 'dataframe:' + o.to_json(orient="table")
        elif isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r[:-6] + "Z"
            return 'datetime:' + r
        elif isinstance(o, datetime.date):
            return 'date:' + o.isoformat()
        elif isinstance(o, datetime.time):
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return 'time:' + r
        elif isinstance(o, decimal.Decimal): 
            return 'decimal:' + str(o)
        elif isinstance(o, uuid.UUID):
            return 'uuid:' + str(o)
        elif isinstance(o, bytes):
            return 'bytes:' + base64.b64encode(o).decode("UTF-8")
        elif hasattr(o, '__dict__'):
            return o.__dict__
        else:
            return super().default(o)

# It's a JSON decoder that looks for a colon in the value of a key/value pair. If it finds one, it
# assumes the value is a string that represents a type and a value. It then converts the value to the
# appropriate type
class IrisJSONDecoder(json.JSONDecoder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj: Dict) -> Dict:
        ret = {}
        for key, value in obj.items():
            i = 0
            if isinstance(value, str):
                i = value.find(":") 
            if (i > 0):
                typ = value[:i]
                if typ == 'datetime':
                    ret[key] = datetime.datetime.fromisoformat(value[i+1:])
                elif typ == 'date':
                    ret[key] = datetime.date.fromisoformat(value[i+1:])
                elif typ == 'time':
                    ret[key] = datetime.time.fromisoformat(value[i+1:])
                elif typ == 'dataframe':
                    module = importlib.import_module('pandas')
                    ret[key] = module.read_json(value[i+1:], orient="table")
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

class _send_request_async_ng(asyncio.Future):

    _message_header_id: int = 0
    _queue_name: str = ""
    _end_time: int = 0
    _response: Any = None
    _done: bool = False

    def __init__(self, target: str, request: Union[Message, Any], 
                 timeout: int = -1, description: Optional[str] = None, host: Optional[_BusinessHost] = None) -> None:
        super().__init__()
        self.target = target
        self.request = request
        self.timeout = timeout
        self.description = description
        self.host = host
        self._iris_handle = host.iris_handle
        asyncio.create_task(self.send())

    async def send(self) -> None:
        # init parameters
        message_header_id = iris.ref()
        queue_name = iris.ref()
        end_time = iris.ref()
        request = self.host._dispatch_serializer(self.request)

        # send request
        self._iris_handle.dispatchSendRequestAsyncNG(
            self.target, request, self.timeout, self.description,
            message_header_id, queue_name, end_time)
        
        # get byref values
        self._message_header_id = message_header_id.value
        self._queue_name = queue_name.value
        self._end_time = end_time.value

        while not self._done:
            await asyncio.sleep(0.1)
            self.is_done()

        self.set_result(self._response)

    def is_done(self) -> None:
        response = iris.ref()
        status = self._iris_handle.dispatchIsRequestDone(self.timeout, self._end_time,
                                                         self._queue_name, self._message_header_id,
                                                         response)
        
        self._response = self.host._dispatch_deserializer(response.value)

        if status == 2: # message found
            self._done = True
        elif status == 1: # message not found
            pass
        else:
            self._done = True
            self.set_exception(RuntimeError(iris.system.Status.GetOneStatusText(status)))
