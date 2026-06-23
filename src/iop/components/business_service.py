import importlib
import warnings
from inspect import signature

from ..messages.decorators import input_deserializer, output_serializer
from .business_host import _BusinessHost


def _accepts_process_input_argument(method) -> bool:
    try:
        return len(signature(method).parameters) > 0
    except (TypeError, ValueError):
        return True


def _call_process_input(method, request):
    if _accepts_process_input_argument(method):
        return method(request)
    return method()


class _BusinessService(_BusinessHost):
    """Runtime base for inbound production entry points.

    IRIS invokes on_process_input(...). By default, that hook delegates to
    on_message(...). Application code should normally subclass iop.BusinessService
    or iop.PollingBusinessService and wire outbound routes with target() in a
    Production graph.
    """

    Adapter = adapter = None
    _wait_for_next_call_interval = False

    def _dispatch_on_init(self, host_object) -> None:
        """For internal use only."""
        self._log_custom_init_warning()
        self.on_init()

        return

    def on_message(self, request=None):
        """Purpose:
            Handle a message received by a BusinessService.

        Use when:
            A service receives data from an adapter, Director API call, or
            custom entry point and should send work into the production graph.

        Lifecycle:
            The default on_process_input(message_input) implementation delegates
            to on_message(message_input).

        Best practices:
            Validate or normalize inbound data, then send a Message to a target
            declared with target().

        Common mistakes:
            Do not call downstream component methods directly. Use
            send_request_async(...) or send_request_sync(...).

        Minimal example:
            def on_message(self, request):
                self.send_request_async(self.Output, request)

        Related:
            docs/cookbooks/add-polling-service.md,
            docs/cookbooks/hl7v2-native-input.md
        """
        warnings.warn(
            f"{self.__class__.__name__} did not override on_message() or "
            "on_process_input(); the incoming service message was ignored. "
            "This default no-op handler will raise NotImplementedError in v5.0.",
            RuntimeWarning,
            stacklevel=2,
        )
        return None

    def on_process_input(self, message_input=None):
        """Handle IRIS ProcessInput and delegate to on_message(message_input).

        Override this low-level hook only when an inbound adapter or Director
        call needs custom ProcessInput handling. For simple services, override
        on_message(...); for scheduled polling, use PollingBusinessService and
        override on_poll().
        """
        return self.on_message(message_input)

    def _set_iris_handles(self, handle_current, handle_partner):
        """For internal use only."""
        self.iris_handle = handle_current
        if type(handle_partner).__module__.find("iris") == 0:
            if handle_partner._IsA("IOP.InboundAdapter"):
                module = importlib.import_module(handle_partner.GetModule())
                handle_partner = getattr(module, handle_partner.GetClassname())()
        self.Adapter = self.adapter = handle_partner
        return

    @input_deserializer
    @output_serializer
    def _dispatch_on_process_input(self, request):
        """For internal use only."""
        return _call_process_input(self.on_process_input, request)
