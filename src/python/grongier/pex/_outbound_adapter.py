from grongier.pex._common import _Common

class _OutboundAdapter(_Common):
    """ Responsible for sending the data to the external system."""
    BusinessHost = None

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