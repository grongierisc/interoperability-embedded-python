import importlib
from inspect import signature
from grongier.pex._business_host import _BusinessHost

class _BusinessOperation(_BusinessHost):
    """ This class corresponds to the PEX framework EnsLib.PEX.BusinessOperation class.
    The EnsLib.PEX.BusinessOperation RemoteClassName property identifies the Python class with the business operation implementation.
    The business operation can optionally use an adapter to handle the outgoing message. Specify the adapter in the OutboundAdapter property.
    If the business operation has an adapter, it uses the adapter to send the message to the external system.
    The adapter can either be a PEX adapter or an ObjectScript adapter.
    """

    DISPATCH = []
    Adapter = None

    def on_message(self, request):
        """ Called when the business operation receives a message from another production component.
        Typically, the operation will either send the message to the external system or forward it to a business process or another business operation.
        If the operation has an adapter, it uses the Adapter.invoke() method to call the method on the adapter that sends the message to the external system.
        If the operation is forwarding the message to another production component, it uses the SendRequestAsync() or the SendRequestSync() method

        Parameters:
        request: An instance of either a subclass of Message or of IRISObject containing the incoming message for the business operation.

        Returns:
        The response object
        """
        return self.OnMessage(request)

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.iris_handle = handle_current
        if type(handle_partner).__module__.find('iris') == 0:
            if handle_partner._IsA("Grongier.PEX.OutboundAdapter"):
                module = importlib.import_module(handle_partner.GetModule())
                handle_partner = getattr(module, handle_partner.GetClassname())()
            self.Adapter = handle_partner
        return

    def _dispatch_on_init(self, host_object):
        """ For internal use only. """
        self._create_dispatch()
        self.on_init()
        return

    def _dispatch_on_message(self, request):
        """ For internal use only. """
        request = self._deserialize_message(request)
        # method dispachMessage
        return_object = self._dispach_message(request)
        return_object = self._serialize_message(return_object)
        return return_object

    def _dispach_message(self, request):
        """
        It takes a request object, and returns a response object
        
        :param request: The request object
        :return: The return value is the result of the method call.
        """

        call = 'on_message'

        module = request.__class__.__module__
        classname = request.__class__.__name__

        for msg,method in self.DISPATCH:
            if msg == module+"."+classname:
                call = method

        return getattr(self,call)(request)

    
    def _create_dispatch(self):
        """
        It creates a list of tuples, where each tuple contains the name of a class and the name of a method
        that takes an instance of that class as its only argument
        :return: A list of tuples.
        """
        if len(self.DISPATCH) == 0:
            #get all function in current BO
            method_list = [func for func in dir(self) if callable(getattr(self, func)) and not func.startswith("_")]
            for method in method_list:
                #get signature of current function
                try:
                    param = signature(getattr(self, method)).parameters
                # Handle staticmethod
                except ValueError as e:
                    param=''
                #one parameter
                if (len(param)==1):
                    #get parameter type
                    annotation = str(param[list(param)[0]].annotation)
                    #trim annotation format <class 'toto'>
                    i = annotation.find("'")
                    j = annotation.rfind("'")
                    #if end is not found
                    if j == -1:
                        j = None
                    classname = annotation[i+1:j]
                    self.DISPATCH.append((classname,method))
        return

    def OnMessage(self, request):
        """ DEPRECATED : use on_message
        Called when the business operation receives a message from another production component.
        Typically, the operation will either send the message to the external system or forward it to a business process or another business operation.
        If the operation has an adapter, it uses the Adapter.invoke() method to call the method on the adapter that sends the message to the external system.
        If the operation is forwarding the message to another production component, it uses the SendRequestAsync() or the SendRequestSync() method

        Parameters:
        request: An instance of either a subclass of Message or of IRISObject containing the incoming message for the business operation.

        Returns:
        The response object
        """
        return 
