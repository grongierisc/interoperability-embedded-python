import datetime
import uuid
import decimal
import base64
import json
import importlib
import iris

from grongier.dacite import from_dict

from grongier.pex._common import _Common

class _BusinessHost(_Common):
    """ This is a superclass for BusinessService, BusinesProcess, and BusinessOperation that
    defines common methods. It is a subclass of Common.
    """

    buffer:int = 64000
        
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

        request = self._serialize_message(request)
        return_object = self.iris_handle.dispatchSendRequestSync(target,request,timeout,description)
        return_object = self._deserialize_message(return_object)
        return return_object

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

        request = self._serialize_message(request)
        self.iris_handle.dispatchSendRequestAsync(target,request,description)
        return

    def _serialize_message(self,message):
        """ Converts a python dataclass message into an iris grongier.pex.message.

        Parameters:
        message: The message to serialize, an instance of a class that is a subclass of Message.

        Returns:
        string: The message in json format.
        """
        if (message is not None and self._is_message_instance(message)):

            json_string = json.dumps(message, cls=IrisJSONEncoder)
            module = message.__class__.__module__
            classname = message.__class__.__name__

            msg = iris.cls('Grongier.PEX.Message')._New()
            msg.classname = module + "." + classname

            stream = iris.cls('%Stream.GlobalCharacter')._New()
            n = self.buffer
            chunks = [json_string[i:i+n] for i in range(0, len(json_string), n)]
            for chunk in chunks:
                stream.Write(chunk)
            msg.jstr = stream

            return msg
        else:
            return message

    def _serialize(self,message):
        """ Converts a message into json format.

        Parameters:
        message: The message to serialize, an instance of a class that is a subclass of Message.

        Returns:
        string: The message in json format.
        """
        if (message is not None):
            json_string = json.dumps(message, cls=IrisJSONEncoder)
            module = message.__class__.__module__
            classname = message.__class__.__name__
            return  module + "." + classname + ":" + json_string
        else:
            return None

    def _deserialize_message(self,serial):
        """ Converts an iris grongier.pex.message into an python dataclass message.
        
        """
        if (type(serial).__module__.find('iris') == 0) and serial._IsA("Grongier.PEX.Message"):
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

            string = ""
            serial.jstr.Rewind()
            while not serial.jstr.AtEnd:
                string += serial.jstr.Read(self.buffer)

            jdict = json.loads(string, cls=IrisJSONDecoder)
            msg = self._dataclass_from_dict(msg,jdict)
            return msg
        else:
            return serial

    def _deserialize(self,serial):
        """ Converts a json string into a message of type classname, which is stored in the json string.

        Parameters:
        serial: The json string to deserialize.

        Returns:
        Message: The message as an instance of the class specified in the json string, which is a subclass of Message.

        Raises:
        ImportError: if the classname does not include a module name to import.
        """
        if (serial is not None and serial != ""):
            i = serial.find(":")
            if (i <=0):
                raise ValueError("JSON message malformed, must include classname: " + serial)
            classname = serial[:i]

            j = classname.rindex(".")
            if (j <=0):
                raise ValueError("Classname must include a module: " + classname)

            try:
                module = importlib.import_module(classname[:j])
                msg = getattr(module, classname[j+1:])
            except Exception:
                raise ImportError("Class not found: " + classname)
            jdict = json.loads(serial[i+1:], cls=IrisJSONDecoder)
            msg = self._dataclass_from_dict(msg,jdict)
            return msg
        else:
            return None

    def _dataclass_from_dict(self,klass, dikt):
        ret = from_dict(klass, dikt)
        
        try:
            fieldtypes = klass.__annotations__
        except Exception as e:
            fieldtypes = []
        
        for key,val in dikt.items():
            if key not in fieldtypes:
                setattr(ret, key, val)
        return ret


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

# It's a subclass of the standard JSONEncoder class that knows how to encode date/time, decimal types,
# and UUIDs.
class IrisJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    """

    def default(self, o):
        if hasattr(o, '__dict__'):
            return o.__dict__
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
                if typ in {'datetime', 'time','date'}:
                    ret[key] = datetime.datetime.fromisoformat(value[i+1:]) 
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
