import json
import sys
import iris
from pex._Common import _Common

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
            serialized = self._serialize(request)
            returnObject = self.irisHandle.invoke("dispatchSendRequestSync",target,serialized,timeout,description)
        elif isinstance(request, iris.IRISObject):
            returnObject = self.irisHandle.invoke("dispatchSendRequestSync",target,request,timeout,description)
        else:
            raise TypeError
        if isinstance(returnObject, str):
            returnObject = self._deserialize(returnObject)
        return returnObject

    @staticmethod
    def _serialize(message):
        """ Converts a message into json format.

        Parameters:
        message: The message to serialize, an instance of a class that is a subclass of Message.

        Returns:
        string: The message in json format.
        """
        if (message != None):
            jString = json.dumps(message.__dict__) 
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
        if (serial != None):
            i = serial.find(":")
            if (i <=0):
                raise ValueError("JSON message malformed, must include classname: " + serial)
            classpath = serial[:i]
            gateway = iris.GatewayContext.getConnection()._get_gateway()
            try:
                klass = gateway._load_class(classpath)
                msg = klass()
            except Exception:
                raise ImportError("Class not found: " + classpath)
            jdict = json.loads(serial[i+1:])
            for k, v in jdict.items():
                setattr(msg, k, v)
            return msg
        else:
            return None
                