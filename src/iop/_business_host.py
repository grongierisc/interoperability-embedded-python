from inspect import getsource
from typing import Any,List, Optional, Tuple, Union

from . import _iris
from ._common import _Common
from ._message import _Message as Message
from ._decorators import input_serializer_param, output_deserializer
from ._dispatch import dispatch_serializer, dispatch_deserializer
from ._async_request import AsyncRequest

class _BusinessHost(_Common):
    """Base class for business components that defines common methods.
    
    This is a superclass for BusinessService, BusinessProcess, and BusinessOperation that
    defines common functionality like message serialization/deserialization and request handling.
    """

    buffer: int = 64000
    DISPATCH: List[Tuple[str, str]] = []

    @input_serializer_param(1, 'request')
    @output_deserializer
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

    @input_serializer_param(1, 'request')
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
        return await AsyncRequest(target, request, timeout, description, self)

    def send_multi_request_sync(self, target_request: List[Tuple[str, Union[Message, Any]]], 
                               timeout: int = -1, description: Optional[str] = None) -> List[Tuple[str, Union[Message, Any], Any, int]]:
        """Send multiple messages synchronously to target components.
        
        Args:
            target_request: List of tuples (target, request) to send
            timeout: Timeout in seconds, -1 means wait forever 
            description: Optional description for logging
            
        Returns:
            List of tuples (target, request, response, status)
            
        Raises:
            TypeError: If target_request is not a list of tuples
            ValueError: If target_request is empty
        """
        self._validate_target_request(target_request)
        
        call_list = [self._create_call_structure(target, request) 
                    for target, request in target_request]
        
        response_list = self.iris_handle.dispatchSendRequestSyncMultiple(call_list, timeout)
        
        return [(target_request[i][0],
                target_request[i][1], 
                dispatch_deserializer(response_list[i].Response),
                response_list[i].ResponseCode) 
                for i in range(len(target_request))]

    def _validate_target_request(self, target_request: List[Tuple[str, Union[Message, Any]]]) -> None:
        """Validate the target_request parameter structure."""
        if not isinstance(target_request, list):
            raise TypeError("target_request must be a list")
        if not target_request:
            raise ValueError("target_request must not be empty")
        if not all(isinstance(item, tuple) and len(item) == 2 for item in target_request):
            raise TypeError("target_request must contain tuples of (target, request)")

    def _create_call_structure(self, target: str, request: Union[Message, Any]) -> Any:
        """Create an Ens.CallStructure object for the request."""
        iris = _iris.get_iris()
        call = iris.cls("Ens.CallStructure")._New()
        call.TargetDispatchName = target
        call.Request = dispatch_serializer(request)
        return call

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
