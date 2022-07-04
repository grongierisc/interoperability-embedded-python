from grongier.pex._common import _Common

class _OutboundAdapter(_Common):
    """ Responsible for sending the data to the external system."""
    BusinessHost = None

    def on_keepalive(self):
        """
        > This function is called when the server sends a keepalive message
        """
        return

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.iris_handle = handle_current
        self.BusinessHost = handle_partner
        return

