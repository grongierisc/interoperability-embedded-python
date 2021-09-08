import grongier.pex
import iris
from grongier.pex._BusinessHost import _BusinessHost

class _BusinessService(_BusinessHost):
    """ This class is responsible for receiving the data from external system and sending it to business processes or business operations in the production.
    The business service can use an adapter to access the external system, which is specified in the InboundAdapter property. 
    There are three ways of implementing a business service:
    1) Polling business service with an adapter - The production framework at regular intervals calls the adapter’s OnTask() method, 
        which sends the incoming data to the the business service ProcessInput() method, which, in turn calls the OnProcessInput method with your code.
    2) Polling business service that uses the default adapter - In this case, the framework calls the default adapter's OnTask method with no data. 
        The OnProcessInput() method then performs the role of the adapter and is responsible for accessing the external system and receiving the data.
    3) Nonpolling business service - The production framework does not initiate the business service. Instead custom code in either a long-running process 
        or one that is started at regular intervals initiates the business service by calling the Director.CreateBusinessService() method.
    """

    def __init__(self):
        """ The Adapter instance variable provides access to the inbound adapter associated with the business service."""
        super().__init__()
        self.Adapter = None
        self._WaitForNextCallInterval = False
    
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

    def OnProcessInput(self, messageInput):
        """ Receives the message from the inbond adapter via the PRocessInput method and is responsible for forwarding it to target business processes or operations.
        If the business service does not specify an adapter, then the default adapter calls this method with no message 
        and the business service is responsible for receiving the data from the external system and validating it.

        Parameters:
        messageInput: an instance of IRISObject or subclass of Message containing the data that the inbound adapter passes in.
            The message can have any structure agreed upon by the inbound adapter and the business service. 
        """
        pass

    @staticmethod
    def getAdapterType():
        """ The getAdapterType() method is called when registering the business service in order to instruct the business service on what inbound adapter to use.
        The return value from this method should be the string name of the inbound adapter class.  This may be an ObjectScript class or a PEX adapter class.
        Return the empty string for adapterless business services.
        """
        return ""

    def _setIrisHandles(self, handleCurrent, handlePartner):
        """ For internal use only. """
        self.irisHandle = handleCurrent
        if type(handlePartner).__module__.find('iris') == 0:
            if handlePartner._IsA("Grongier.PEX.InboundAdapter"):
                module = __import__(handlePartner.GetModule())
                handlePartner = getattr(module, handlePartner.GetClassname())()
        self.Adapter = handlePartner
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
    
