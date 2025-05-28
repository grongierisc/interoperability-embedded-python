from typing import Any, List, Optional, Union

from ._business_host import _BusinessHost
from ._decorators import input_deserializer, input_serializer_param, output_serializer, input_serializer, output_deserializer
from ._dispatch import create_dispatch, dispach_message

class _BusinessProcess(_BusinessHost):
    """Business process component that contains routing and transformation logic.
    
    A business process can receive messages from services, other processes, or operations.
    It can modify messages, transform formats, and route based on content.
    """

    DISPATCH: List[tuple] = []
    PERSISTENT_PROPERTY_LIST: Optional[List[str]] = None

    def on_message(self, request: Any) -> Any:
        """Handle incoming messages.

        Args:
            request: The incoming message

        Returns:
            Response message
        """
        return self.on_request(request)

    def on_request(self, request: Any) -> Any:
        """Process initial requests sent to this component.
        
        Args:
            request: The incoming request message
            
        Returns:
            Response message
        """
        return self.OnRequest(request)

    def on_response(self, request: Any, response: Any, call_request: Any, call_response: Any, completion_key: str) -> Any:
        """Handle responses to messages sent by this component.
        
        Args:
            request: The initial request message
            response: The response message
            call_request: The request sent to the target
            call_response: The incoming response
            completion_key: The completion key specified in the outgoing SendAsync() method
            
        Returns:
            Response message
        """
        return self.OnResponse(request, response, call_request, call_response, completion_key)

    def on_complete(self, request: Any, response: Any) -> Any:
        """Called after all responses to requests sent by this component have been handled.
        
        Args:
            request: The initial request message
            response: The response message
            
        Returns:
            Response message
        """
        return self.OnComplete(request, response)

    @input_serializer_param(0,'response')
    def reply(self, response: Any) -> None:
        """Send the specified response to the production component that sent the initial request.

        Args:
            response: The response message
        """
        return self.iris_handle.dispatchReply(response)
    
    @input_serializer_param(1,'request')
    def send_request_async(self, target: str, request: Any, description: Optional[str]=None, completion_key: Optional[str]=None, response_required: bool=True) -> None:
        """Send the specified message to the target business process or business operation asynchronously.
        
        Args:
            target: The name of the business process or operation to receive the request
            request: The message to send to the target
            description: An optional description property in the message header
            completion_key: A string that will be returned with the response if the maximum time is exceeded
            response_required: Whether a response is required
            
        Raises:
            TypeError: If request is not of type Message or IRISObject
        """
        if response_required:
            response_required = True
        else:
            response_required = False
        return self.iris_handle.dispatchSendRequestAsync(target, request, response_required, completion_key, description)

    def set_timer(self, timeout: Union[int, str], completion_key: Optional[str]=None) -> None:
        """Specify the maximum time the business process will wait for responses.

        Args:
            timeout: The maximum time to wait for responses
            completion_key: A string that will be returned with the response if the maximum time is exceeded
        """
        self.iris_handle.dispatchSetTimer(timeout, completion_key)
        return

    def _set_iris_handles(self, handle_current: Any, handle_partner: Any) -> None:
        """For internal use only."""
        self.iris_handle = handle_current
        return

    def _save_persistent_properties(self, host_object: Any) -> None:
        """For internal use only."""
        if self.PERSISTENT_PROPERTY_LIST is None:
            return
        for prop in self.PERSISTENT_PROPERTY_LIST:
            val = getattr(self, prop, None)
            typ = val.__class__.__name__
            if typ in ["str", "int", "float", "bool", "bytes"]:
                try:
                    host_object.setPersistentProperty(prop, val)
                except:
                    pass
        return

    def _restore_persistent_properties(self, host_object: Any) -> None:
        """For internal use only."""
        if self.PERSISTENT_PROPERTY_LIST is None:
            return
        for prop in self.PERSISTENT_PROPERTY_LIST:
            try:
                val = host_object.getPersistentProperty(prop)
                setattr(self, prop, val)
            except:
                pass
        return

    def _dispatch_on_connected(self, host_object: Any) -> None:
        """For internal use only."""
        self.on_connected()
        self._save_persistent_properties(host_object)
        return

    def _dispatch_on_init(self, host_object: Any) -> None:
        """For internal use only."""
        self._restore_persistent_properties(host_object)
        create_dispatch(self)
        self.on_init()
        self._save_persistent_properties(host_object)
        return

    def _dispatch_on_tear_down(self, host_object: Any) -> None:
        """For internal use only."""
        self._restore_persistent_properties(host_object)
        self.on_tear_down()
        self._save_persistent_properties(host_object)
        return

    @input_deserializer
    @output_serializer
    def _dispatch_on_request(self, host_object: Any, request: Any) -> Any:
        """For internal use only."""
        self._restore_persistent_properties(host_object)
        return_object = dispach_message(self,request)
        self._save_persistent_properties(host_object)
        return return_object
    
    @input_deserializer
    @output_serializer
    def _dispatch_on_response(self, host_object: Any, request: Any, response: Any, call_request: Any, call_response: Any, completion_key: str) -> Any:
        """For internal use only."""
        self._restore_persistent_properties(host_object)
        return_object = self.on_response(request, response, call_request, call_response, completion_key)
        self._save_persistent_properties(host_object)
        return return_object

    @input_deserializer
    @output_serializer
    def _dispatch_on_complete(self, host_object: Any, request: Any, response: Any) -> Any:
        """For internal use only."""
        self._restore_persistent_properties(host_object)
        return_object = self.on_complete(request, response)
        self._save_persistent_properties(host_object)
        return return_object

    def OnRequest(self, request: Any) -> Any:
        """ 
        DEPRECATED: Use on_request.
        
        Args:
            request: The incoming request message
            
        Returns:
            Response message
        """
        return 

    def OnResponse(self, request: Any, response: Any, call_request: Any, call_response: Any, completion_key: str) -> Any:
        """ 
        DEPRECATED: Use on_response.
        
        Args:
            request: The initial request message
            response: The response message
            call_request: The request sent to the target
            call_response: The incoming response
            completion_key: The completion key specified in the outgoing SendAsync() method
            
        Returns:
            Response message
        """
        return response

    def OnComplete(self, request: Any, response: Any) -> Any:
        """ 
        DEPRECATED: Use on_complete.
        
        Args:
            request: The initial request message
            response: The response message
            
        Returns:
            Response message
        """
        return response