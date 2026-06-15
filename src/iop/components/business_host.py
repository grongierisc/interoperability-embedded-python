import ast
import textwrap
from inspect import getsource
from typing import Any, cast

from ..messages.base import _Message as Message
from ..messages.decorators import (
    input_deserializer,
    input_serializer_param,
    output_deserializer,
    output_serializer,
)
from ..messages.dispatch import (
    dispatch_deserializer,
    dispatch_message,
    dispatch_serializer,
)
from ..production import TargetSettingRef, resolve_target
from ..runtime import iris as _iris
from .async_request import AsyncRequest
from .common import _Common
from .generator_request import _GeneratorRequest

_CONNECTION_METHODS = {
    "send_request_sync",
    "send_request_async",
    "send_request_async_ng",
    "send_generator_request",
}
_UNRESOLVED = object()


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _call_target_node(call: ast.Call) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == "target":
            return keyword.value
    if call.args:
        return call.args[0]
    return None


def _resolve_connection_target(host: Any, node: ast.AST) -> Any:
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError):
        value = _UNRESOLVED
    if isinstance(value, str):
        return value

    if isinstance(node, ast.Name):
        return getattr(host, node.id, _UNRESOLVED)

    if isinstance(node, ast.Attribute):
        return _resolve_attribute_target(host, node)

    return _UNRESOLVED


def _resolve_attribute_target(host: Any, node: ast.Attribute) -> Any:
    chain = []
    current: ast.AST = node
    while isinstance(current, ast.Attribute):
        chain.append(current.attr)
        current = current.value

    if isinstance(current, ast.Name):
        if current.id == "self":
            value = host
        else:
            value = getattr(host, current.id, _UNRESOLVED)
    else:
        return _UNRESOLVED

    for attr in reversed(chain):
        if value is _UNRESOLVED:
            return _UNRESOLVED
        value = getattr(value, attr, _UNRESOLVED)
    return value


class _BusinessHost(_Common):
    """Base class for business components that defines common methods.

    This is a superclass for BusinessService, BusinessProcess, and BusinessOperation that
    defines common functionality like message serialization/deserialization and request handling.
    App code should normally call send_request_* with target() attributes such
    as self.Output instead of hard-coded component names. See
    docs/cookbooks/production-settings-and-targets.md.
    """

    buffer: int = 64000
    DISPATCH: list[tuple[str, str]] = []

    @input_serializer_param(1, "request")
    @output_deserializer
    def send_request_sync(
        self,
        target: str | TargetSettingRef,
        request: Message | Any,
        timeout: int = -1,
        description: str | None = None,
    ) -> Any:
        """Purpose:
            Send a message to a target component and wait for the response.

        Use when:
            The caller needs the target response before continuing.

        Lifecycle:
            IoP serializes request, calls the IRIS synchronous dispatch API, and
            deserializes the response before returning.

        Best practices:
            Pass a target() attribute such as self.Output so the route is
            configurable in the Production graph.

        Common mistakes:
            Do not use synchronous calls for long-running work unless the caller
            really must block.

        Minimal example:
            response = self.send_request_sync(self.Output, request)

        Related:
            docs/cookbooks/add-business-process.md,
            docs/cookbooks/production-settings-and-targets.md
        """
        target = resolve_target(target)
        return self.iris_handle.dispatchSendRequestSync(
            target, request, timeout, description
        )

    @input_serializer_param(1, "request")
    def send_request_async(
        self,
        target: str | TargetSettingRef,
        request: Message | Any,
        description: str | None = None,
    ) -> None:
        """Purpose:
            Send a message to a target component without waiting for a response.

        Use when:
            A service or operation should enqueue downstream work and continue.

        Lifecycle:
            IoP serializes request and calls the IRIS asynchronous dispatch API.

        Best practices:
            Pass a target() attribute such as self.Output so the route is
            configurable in the Production graph.

        Common mistakes:
            Do not use this helper when the caller requires a response; use
            send_request_sync(...) or the BusinessProcess async response flow.

        Minimal example:
            self.send_request_async(self.Output, request)

        Related:
            docs/cookbooks/add-polling-service.md,
            docs/cookbooks/production-settings-and-targets.md
        """
        target = resolve_target(target)
        return self.iris_handle.dispatchSendRequestAsync(target, request, description)

    async def send_request_async_ng(
        self,
        target: str | TargetSettingRef,
        request: Message | Any,
        timeout: int = -1,
        description: str | None = None,
    ) -> Any:
        """Send message asynchronously to target component with asyncio.

        Prefer a target() attribute such as self.Output for configurable
        routing. Use this helper when the component method is already async.

        Args:
            target: Name of target component
            request: Message to send
            timeout: Timeout in seconds, -1 means wait forever
            description: Optional description for logging

        Returns:
            Response from target component
        """
        target = cast(str, resolve_target(target))
        return await AsyncRequest(target, request, timeout, description, self)

    def send_generator_request(
        self,
        target: str | TargetSettingRef,
        request: Message | Any,
        timeout: int = -1,
        description: str | None = None,
    ) -> _GeneratorRequest:
        """Send message as a generator request to target component.

        Prefer a target() attribute such as self.Output for configurable
        routing.

        Args:
            target: Name of target component
            request: Message to send
            timeout: Timeout in seconds, -1 means wait forever
            description: Optional description for logging
        Returns:
            _GeneratorRequest: An instance of _GeneratorRequest to iterate over responses
        Raises:
            TypeError: If request is not of type Message
        """
        target = cast(str, resolve_target(target))
        return _GeneratorRequest(self, target, request, timeout, description)

    def send_multi_request_sync(
        self,
        target_request: list[tuple[str | TargetSettingRef, Message | Any]],
        timeout: int = -1,
        description: str | None = None,
    ) -> list[tuple[str, Message | Any, Any, int]]:
        """Send multiple messages synchronously to target components.

        Each target can be a target() attribute such as self.Accepted or a
        component name. Prefer target() attributes for configurable production
        graphs.

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
        resolved_target_request: list[tuple[str, Message | Any]] = [
            (resolve_target(target), request) for target, request in target_request
        ]

        call_list = [
            self._create_call_structure(target, request)
            for target, request in resolved_target_request
        ]

        response_list = self.iris_handle.dispatchSendRequestSyncMultiple(
            call_list, timeout
        )

        return [
            (
                resolved_target_request[i][0],
                resolved_target_request[i][1],
                dispatch_deserializer(response_list[i].Response),
                int(response_list[i].ResponseCode),
            )
            for i in range(len(resolved_target_request))
        ]

    def _validate_target_request(
        self, target_request: list[tuple[str | TargetSettingRef, Message | Any]]
    ) -> None:
        """Validate the target_request parameter structure."""
        if not isinstance(target_request, list):
            raise TypeError("target_request must be a list")
        if not target_request:
            raise ValueError("target_request must not be empty")
        if not all(
            isinstance(item, tuple) and len(item) == 2 for item in target_request
        ):
            raise TypeError("target_request must contain tuples of (target, request)")

    def _create_call_structure(
        self, target: str | TargetSettingRef, request: Message | Any
    ) -> Any:
        """Create an Ens.CallStructure object for the request."""
        iris = _iris.get_iris()
        call = iris.cls("Ens.CallStructure")._New()
        call.TargetDispatchName = resolve_target(target)
        call.Request = dispatch_serializer(request)
        return call

    @staticmethod
    def OnGetConnections() -> list[str] | None:
        """Return all configured targets for this class.

        Implement this method to allow connections between components to show up
        in the interoperability UI.

        Returns:
            An IRISList containing all targets for this class. Default is None.
        """
        return None

    @staticmethod
    def get_adapter_type() -> str | None:
        """Returns the name of the registered Adapter.

        Returns:
            Name of the registered Adapter
        """
        return

    def on_get_connections(self) -> list[str]:
        """Return targets found in send_request_sync and send_request_async calls.

        Implement this method to allow connections between components to show up
        in the interoperability UI.

        Returns:
            A list containing all targets for this class.
        """
        source = textwrap.dedent(getsource(self.__class__))
        tree = ast.parse(source)
        target_list: list[str] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if _call_name(node.func) not in _CONNECTION_METHODS:
                continue

            target_node = _call_target_node(node)
            if target_node is None:
                continue

            target = _resolve_connection_target(self, target_node)
            if isinstance(target, str) and target not in target_list:
                target_list.append(target)

        return target_list

    @input_deserializer
    def _dispatch_generator_started(self, request: Any) -> Any:
        """For internal use only."""
        self._gen = dispatch_message(self, request)
        # check if self._gen is a generator
        if not hasattr(self._gen, "__iter__"):
            raise TypeError(
                f"Expected a generator or iterable object, got: {type(self._gen).__name__}"
            )

        return _iris.get_iris().IOP.Generator.Message.Ack._New()

    @output_serializer
    def _dispatch_generator_poll(self) -> Any:
        """For internal use only."""
        try:
            return next(self._gen)
        except StopIteration:
            return _iris.get_iris().IOP.Generator.Message.Stop._New()
