import warnings


class _PollingBusinessServiceMixin:
    """Mixin for services polled by the default IRIS inbound adapter."""

    @staticmethod
    def get_adapter_type() -> str:
        return "Ens.InboundAdapter"

    def on_poll(self):
        """Run one scheduled polling cycle.

        Override this for services that are called by the default IRIS inbound
        adapter and fetch their own external data.
        """
        warnings.warn(
            f"{self.__class__.__name__} did not override on_poll() or "
            "on_process_input(); the scheduled poll was ignored. "
            "This default no-op handler will raise NotImplementedError in v5.0.",
            RuntimeWarning,
            stacklevel=2,
        )
        return None

    def on_process_input(self, message_input=None):
        """Compatibility hook called by IRIS ProcessInput."""
        return self.on_poll()
