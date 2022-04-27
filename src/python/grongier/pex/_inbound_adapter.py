from grongier.pex._common import _Common

class _InboundAdapter(_Common):
    """ Responsible for receiving the data from the external system, validating the data, 
    and sending it to the business service by calling the BusinessHost.ProcessInput() method.
    """
    BusinessHost = None

    def on_task(self): 
        """ Called by the production framework at intervals determined by the business service CallInterval property.
        It is responsible for receiving the data from the external system, validating the data, and sending it in a message to the business service OnProcessInput method.
        The message can have any structure agreed upon by the inbound adapter and the business service.
        """

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

    def OnTask(self):
        """  DEPRECATED : use on_task
        Called by the production framework at intervals determined by the business service CallInterval property.
        It is responsible for receiving the data from the external system, validating the data, and sending it in a message to the business service OnProcessInput method.
        The message can have any structure agreed upon by the inbound adapter and the business service.
        """
        return  self.on_task()