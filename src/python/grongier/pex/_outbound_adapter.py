from grongier.pex._common import _Common

class _OutboundAdapter(_Common):
    """ Responsible for sending the data to the external system."""

    def __init__(self):
        """ The BusinessHost variable provides access to the BusinessOperation associated with the OutboundAdapter."""
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
        

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.iris_handle = handle_current
        self.BusinessHost = handle_partner
        return

    def _dispatch_on_connected(self):
        """ For internal use only. """
        self.on_connected()
        return

    def _dispatch_on_init(self):
        """ For internal use only. """
        self.on_init()
        return

    def _dispatch_on_tear_down(self):
        """ For internal use only. """
        self.on_tear_down()
        return