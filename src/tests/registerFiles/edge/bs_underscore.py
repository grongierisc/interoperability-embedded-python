from grongier.pex import BusinessService

class BS(BusinessService):

    @staticmethod
    def get_adapter_type():
        return 'EnsLib.File.InboundAdapter'