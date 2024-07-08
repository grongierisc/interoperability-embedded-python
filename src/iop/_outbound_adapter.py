from iop._common import _Common

class _OutboundAdapter(_Common):
    """ Responsible for sending the data to the external system."""
    BusinessHost = business_host = business_host_python = None

    def on_keepalive(self):
        """
        > This function is called when the server sends a keepalive message
        """
        return

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

