import warnings


class _PollingBusinessServiceMixin:
    """Mixin for services polled by the default IRIS inbound adapter."""

    @staticmethod
    def get_adapter_type() -> str:
        return "Ens.InboundAdapter"

    def on_poll(self):
        """Purpose:
            Run one scheduled polling cycle.

        Use when:
            A PollingBusinessService fetches or discovers new work from Python.

        Lifecycle:
            The default IRIS inbound adapter calls on_process_input(), and this
            mixin delegates that call to on_poll().

        Best practices:
            Do a bounded unit of work, then return. Send produced messages with
            send_request_async(self.Output, message).

        Common mistakes:
            Do not create an infinite loop inside on_poll(); use the production
            schedule or call interval for repeated execution.

        Minimal example:
            def on_poll(self):
                self.send_request_async(self.Output, PollRequest())

        Related:
            docs/cookbooks/add-polling-service.md
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
