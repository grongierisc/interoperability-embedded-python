import iris

class _Director():
    """ The Directorclass is used for nonpolling business services, that is, business services which are not automatically
    called by the production framework (through the inbound adapter) at the call interval.
    Instead these business services are created by a custom application by calling the Director.CreateBusinessService() method.
    """

    @staticmethod
    def CreateBusinessService(connection, target):
        """ The CreateBusinessService() method initiates the specifiied business service.

        Parameters:
        connection: an IRISConnection object that specifies the connection to an IRIS instance for Java.
        target: a string that specifies the name of the business service in the production definition.

        Returns:
            an object that contains an instance of IRISBusinessService
        """
        irisInstance = iris.IRIS(connection)
        irisobject = irisInstance.classMethodObject("EnsLib.PEX.Director","dispatchCreateBusinessService",target)
        service = iris.pex._IRISBusinessService._IRISBusinessService()
        service.irisHandle = irisobject
        return service