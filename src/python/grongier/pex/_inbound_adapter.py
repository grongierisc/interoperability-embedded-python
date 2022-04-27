from grongier.pex._common import _Common

class _InboundAdapter(_Common):
    """ Responsible for receiving the data from the external system, validating the data, 
    and sending it to the business service by calling the business_host.ProcessInput() method.
    """

    def __init__(self):
        """ The business_host variable provides access to the business service associated with the inbound adapter.
        The adapter calls the IRISBusinessService.ProcessInput() method of the business service.
        """
        super().__init__()
        self.business_host = None
    
    def on_connected(self):
        """ The on_connected() method is called when the component is connected or reconnected after being disconnected.
        Use the on_connected() method to initialize any structures needed by the component."""
        

    def on_init(self):
        """ The on_init() method is called when the component is started.
        Use the on_init() method to initialize any structures needed by the component."""
        

    def on_tear_down(self):
        """ Called before the component is terminated. Use it to freee any structures."""
        

    def on_task(self):
        """ Called by the production framework at intervals determined by the business service CallInterval property.
        It is responsible for receiving the data from the external system, validating the data, and sending it in a message to the business service OnProcessInput method.
        The message can have any structure agreed upon by the inbound adapter and the business service.
        """
        

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.iris_handle = handle_current
        self.business_host = handle_partner
        return

    def _dispatch_on_connected(self, hostObject):
        """ For internal use only. """
        self.on_connected()
        return

    def _dispatch_on_init(self, hostObject):
        """ For internal use only. """
        self.on_init()
        return

    def _dispatch_on_tear_down(self, hostObject):
        """ For internal use only. """
        self.on_tear_down()
        return