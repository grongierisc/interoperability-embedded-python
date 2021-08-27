class _IRISBusinessService:
    """ Class for proxy objects that represent business service instances in IRIS"""

    def __init__(self):
        self.irisHandle = None

    def ProcessInput(self, input):
        """ Send an object to the business service instance.

        Parameters:
        input: an object to be sent to the business service.

        Returns:
        the object that is returned from the business service.
        """
        return (self.irisHandle._iris).classMethodObject("EnsLib.PEX.BusinessService", "dispatchProcessInput", self.irisHandle, input)

        