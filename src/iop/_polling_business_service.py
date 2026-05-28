class _PollingBusinessServiceMixin:
    """Mixin for services polled by the default IRIS inbound adapter."""

    @staticmethod
    def get_adapter_type() -> str:
        return "Ens.InboundAdapter"
