import importlib

from ..messages.decorators import input_deserializer, output_serializer
from .business_host import _BusinessHost


class _BusinessService(_BusinessHost):
    """This class is responsible for receiving the data from external system and sending it to business processes or business operations in the production.
    The business service can use an adapter to access the external system, which is specified in the InboundAdapter property.
    There are three ways of implementing a business service:
    1) Polling business service with an adapter - The production framework at regular intervals calls the adapter's task method,
        which sends incoming data to the business service process input method.
    2) Polling business service that uses the default adapter - In this case, the framework calls the default adapter's OnTask method with no data.
        The on_process_input() method then performs the role of the adapter and is responsible for accessing the external system and receiving the data.
    3) Nonpolling business service - The production framework does not initiate the business service. Instead custom code in either a long-running process
        or one that is started at regular intervals initiates the business service through the Director API.
    """

    Adapter = adapter = None
    _wait_for_next_call_interval = False

    def _dispatch_on_init(self, host_object) -> None:
        """For internal use only."""
        self.on_init()

        return

    def on_process_input(self, message_input):
        """Receives the message from the inbond adapter via the PRocessInput method and is responsible for forwarding it to target business processes or operations.
        If the business service does not specify an adapter, then the default adapter calls this method with no message
        and the business service is responsible for receiving the data from the external system and validating it.

        Parameters:
        message_input: an instance of IRISObject or subclass of Message containing the data that the inbound adapter passes in.
            The message can have any structure agreed upon by the inbound adapter and the business service.
        """
        return None

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
        return self.on_process_input(request)
