import datetime,uuid,decimal,base64,json,importlib

from grongier.pex._common import _Common

class _BusinessHost(_Common):
    """ This is a superclass for BusinessService, BusinesProcess, and BusinessOperation that
    defines common methods. It is a subclass of Common.
    """

    def __init__(self):
        super().__init__()

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
        if self._is_message_instance(request):
            request = self._serialize(request)
        returnObject = self.irisHandle.dispatchSendRequestSync(target,request,timeout,description)
        if self._is_message_instance(returnObject):
            returnObject = self._deserialize(returnObject)
        return returnObject

    def SendRequestAsync(self, target, request, description=None):
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
        if self._is_message_instance(request):
            request = self._serialize(request)
        self.irisHandle.dispatchSendRequestAsync(target,request,description)
        return


    @staticmethod
    def _serialize(message):
        """ Converts a message into json format.

        Parameters:
        message: The message to serialize, an instance of a class that is a subclass of Message.

        Returns:
        string: The message in json format.
        """
        if (message != None):
            jString = json.dumps(message, cls=IrisJSONEncoder)
            module = message.__class__.__module__
            classname = message.__class__.__name__
            return  module + "." + classname + ":" + jString
        else:
            return None

    @staticmethod
    def _deserialize(serial):
        """ Converts a json string into a message of type classname, which is stored in the json string.

        Parameters:
        serial: The json string to deserialize.

        Returns:
        Message: The message as an instance of the class specified in the json string, which is a subclass of Message.

        Raises:
        ImportError: if the classname does not include a module name to import.
        """
        if (serial != None and serial != ""):
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
            msg = _BusinessHost.dataclass_from_dict(msg,jdict)
            return msg
        else:
            return None

    @staticmethod
    def dataclass_from_dict(klass, dikt):
        try:
            fieldtypes = klass.__annotations__
            for f in dikt:
                test = _BusinessHost.dataclass_from_dict(fieldtypes[f], dikt[f])
            return klass(**{f: _BusinessHost.dataclass_from_dict(fieldtypes[f], dikt[f]) for f in dikt})
        except AttributeError:
            if isinstance(dikt, (tuple, list)):
                return [_BusinessHost.dataclass_from_dict(klass.__args__[0], f) for f in dikt]
            return dikt

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
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
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
