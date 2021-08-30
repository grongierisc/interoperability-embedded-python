import iris
import grongier.pex

class _Director():
    """ The Directorclass is used for nonpolling business services, that is, business services which are not automatically
    called by the production framework (through the inbound adapter) at the call interval.
    Instead these business services are created by a custom application by calling the Director.CreateBusinessService() method.
    """

    @staticmethod
    def CreateBusinessService(target):
        """ The CreateBusinessService() method initiates the specifiied business service.

        Parameters:
        connection: an IRISConnection object that specifies the connection to an IRIS instance for Java.
        target: a string that specifies the name of the business service in the production definition.

        Returns:
            an object that contains an instance of IRISBusinessService
        """
        irisobject = iris.cls("Grongier.PEX.Director").dispatchCreateBusinessService(target)
        return irisobject