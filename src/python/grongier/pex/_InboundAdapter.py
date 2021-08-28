import iris
import grongier.pex
from grongier.pex._Common import _Common

class _InboundAdapter(_Common):
    """ Responsible for receiving the data from the external system, validating the data, 
    and sending it to the business service by calling the BusinessHost.ProcessInput() method.
    """

    def __init__(self):
        """ The BusinessHost variable provides access to the business service associated with the inbound adapter.
        The adapter calls the IRISBusinessService.ProcessInput() method of the business service.
        """
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

    def OnTask(self):
        """ Called by the production framework at intervals determined by the business service CallInterval property.
        It is responsible for receiving the data from the external system, validating the data, and sending it in a message to the business service OnProcessInput method.
        The message can have any structure agreed upon by the inbound adapter and the business service.
        """
        pass

    def _setIrisHandles(self, handleCurrent, handlePartner):
        """ For internal use only. """
        self.irisHandle = handleCurrent
        self.BusinessHost = grongier.pex.IRISBusinessService()
        self.BusinessHost.irisHandle = handlePartner
        return

    def _dispatchOnConnected(self, hostObject):
        """ For internal use only. """
        self.OnConnected()
        return

    def _dispatchOnInit(self, hostObject):
        """ For internal use only. """
        self.OnInit()
        return

    def _dispatchOnTearDown(self, hostObject):
        """ For internal use only. """
        self.OnTearDown()
        return