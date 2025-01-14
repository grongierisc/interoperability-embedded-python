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
from iop._decorators import (
    input_serializer, input_serializer_param, output_deserializer,
    input_deserializer, output_serializer
)
from iop._serialization import IrisJSONEncoder, IrisJSONDecoder
from iop._dispatch import (
    dispatch_serializer, dispatch_deserializer, 
    dispach_message, create_dispatch
)
from iop._async_request import AsyncRequest

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
            call.Request = dispatch_serializer(request)
            call_list.append(call)
        # call the dispatchSendMultiRequestSync method
        response_list = self.iris_handle.dispatchSendRequestSyncMultiple(call_list, timeout)
        # create a list of tuple (target, request, response, status)
        result = []
        for i in range(len(target_request)):
            result.append(
                (target_request[i][0],
                 target_request[i][1],
                 dispatch_deserializer(response_list[i].Response),
                 response_list[i].ResponseCode
                ))
        return result

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
