from iop._common import _Common

class _InboundAdapter(_Common):
    """ Responsible for receiving the data from the external system, validating the data, 
    and sending it to the business service by calling the BusinessHost.ProcessInput() method.
    """
    BusinessHost = business_host = business_host_python = None

    def on_task(self): 
        """ Called by the production framework at intervals determined by the business service CallInterval property.
        It is responsible for receiving the data from the external system, validating the data, and sending it in a message to the business service OnProcessInput method.
        The message can have any structure agreed upon by the inbound adapter and the business service.
        """
        return self.OnTask()

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.iris_handle = handle_current
        self.BusinessHost = handle_partner
        self.business_host = handle_partner
        try:
            self.business_host_python = handle_partner.GetClass()
        except:
            pass
        return


    def OnTask(self):
        """  DEPRECATED : use on_task
        Called by the production framework at intervals determined by the business service CallInterval property.
        It is responsible for receiving the data from the external system, validating the data, and sending it in a message to the business service OnProcessInput method.
        The message can have any structure agreed upon by the inbound adapter and the business service.
        """
        return 