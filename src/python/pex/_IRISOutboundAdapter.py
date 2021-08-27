class _IRISOutboundAdapter:
    """ Class for proxy objects that represent outbound adapter instances in IRIS."""

    def __init__(self):
        self.irisHandle = None
    
    def invoke(self, method, *args):
        """ Invoke a method of the outbound adapter instance.

        Parameters:
        method: string, name of the method to be invoked.
        args: arguments of the invocation.

        Returns:
        the return value of the invocation.
        """
        return self.irisHandle.invoke(method, *args)