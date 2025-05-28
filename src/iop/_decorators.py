from functools import wraps
from typing import Any, Callable

from ._dispatch import dispatch_deserializer, dispatch_serializer

def input_serializer(fonction: Callable) -> Callable:
    """Decorator that serializes all input arguments."""
    def _dispatch_serializer(self, *params: Any, **param2: Any) -> Any:
        serialized = [dispatch_serializer(param) for param in params]
        param2 = {key: dispatch_serializer(value) for key, value in param2.items()}
        return fonction(self, *serialized, **param2)
    return _dispatch_serializer

def input_serializer_param(position: int, name: str) -> Callable:
    """Decorator that serializes specific parameter by position or name."""
    def _input_serializer_param(fonction: Callable) -> Callable:
        @wraps(fonction) 
        def _dispatch_serializer(self, *params: Any, **param2: Any) -> Any:
            serialized = [
                dispatch_serializer(param) if i == position else param
                for i, param in enumerate(params)
            ]
            param2 = {
                key: dispatch_serializer(value) if key == name else value
                for key, value in param2.items()
            }
            return fonction(self, *serialized, **param2)
        return _dispatch_serializer
    return _input_serializer_param

def output_deserializer(fonction: Callable) -> Callable:
    """Decorator that deserializes function output."""
    def _dispatch_deserializer(self, *params: Any, **param2: Any) -> Any:
        return dispatch_deserializer(fonction(self, *params, **param2))
    return _dispatch_deserializer

def input_deserializer(fonction: Callable) -> Callable:
    """Decorator that deserializes all input arguments."""
    def _dispatch_deserializer(self, *params: Any, **param2: Any) -> Any:
        serialized = [dispatch_deserializer(param) for param in params]
        param2 = {key: dispatch_deserializer(value) for key, value in param2.items()}
        return fonction(self, *serialized, **param2)
    return _dispatch_deserializer

def output_serializer(fonction: Callable) -> Callable:
    """Decorator that serializes function output."""
    def _dispatch_serializer(self, *params: Any, **param2: Any) -> Any:
        return dispatch_serializer(fonction(self, *params, **param2))
    return _dispatch_serializer
