from grongier.pex._common import _Common

class _OutboundAdapter(_Common):
    """ Responsible for sending the data to the external system."""
    BusinessHost = None

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.iris_handle = handle_current
        self.BusinessHost = handle_partner
        return
