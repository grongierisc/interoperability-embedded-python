from grongier.pex._common import _Common

class _OutboundAdapter(_Common):
    """ Responsible for sending the data to the external system."""

    def __init__(self):
        """ The BusinessHost variable provides access to the BusinessOperation associated with the OutboundAdapter."""
        super().__init__()
        self.BusinessHost = None
    
    def OnConnected(self):
        """ The OnConnected() method is called when the component is connected or reconnected after being disconnected.
        Use the OnConnected() method to initialize any structures needed by the component."""
        pass

    def OnInit(self):
        """ The OnInit() method is called when the component is started.
        Use the OnInit() method to initialize any structures needed by the component."""
        pass

    def OnTearDown(self):
        """ Called before the component is terminated. Use it to freee any structures."""
        pass

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.irisHandle = handle_current
        self.BusinessHost = handle_partner
        return

    def _dispatch_on_connected(self, host_object):
        """ For internal use only. """
        self.OnConnected()
        return

    def _dispatch_on_init(self, host_object):
        """ For internal use only. """
        self.OnInit()
        return

    def _dispatch_on_tear_down(self, host_object):
        """ For internal use only. """
        self.OnTearDown()
        return