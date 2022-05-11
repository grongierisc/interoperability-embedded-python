import iris

class _Director():
    """ The Directorclass is used for nonpolling business services, that is, business services which are not automatically
    called by the production framework (through the inbound adapter) at the call interval.
    Instead these business services are created by a custom application by calling the Director.CreateBusinessService() method.
    """

    @staticmethod
    def CreateBusinessService(target):
        """ DEPRECATED : use create_business_service
        The CreateBusinessService() method initiates the specifiied business service.

        Parameters:
        connection: an IRISConnection object that specifies the connection to an IRIS instance for Java.
        target: a string that specifies the name of the business service in the production definition.

        Returns:
            an object that contains an instance of IRISBusinessService
        """
        return _Director.create_business_service(target)

    @staticmethod
    def create_business_service(target):
        """ The create_business_service() method initiates the specified business service.

        Parameters:
        connection: an IRISConnection object that specifies the connection to an IRIS instance for Java.
        target: a string that specifies the name of the business service in the production definition.

        Returns:
            an object that contains an instance of IRISBusinessService
        """
        iris_object = iris.cls("Grongier.PEX.Director").dispatchCreateBusinessService(target)
        return iris_object

import iris

class _Director():
    """ The Directorclass is used for nonpolling business services, that is, business services which are not automatically
    called by the production framework (through the inbound adapter) at the call interval.
    Instead these business services are created by a custom application by calling the Director.CreateBusinessService() method.
    """

    @staticmethod
    def CreateBusinessService(target):
        """ DEPRECATED : use create_business_service
        The CreateBusinessService() method initiates the specifiied business service.

        Parameters:
        connection: an IRISConnection object that specifies the connection to an IRIS instance for Java.
        target: a string that specifies the name of the business service in the production definition.

        Returns:
            an object that contains an instance of IRISBusinessService
        """
        return _Director.create_business_service(target)

    @staticmethod
    def create_business_service(target):
        """ The create_business_service() method initiates the specified business service.

        Parameters:
        connection: an IRISConnection object that specifies the connection to an IRIS instance for Java.
        target: a string that specifies the name of the business service in the production definition.

        Returns:
            an object that contains an instance of IRISBusinessService
        """
        iris_object = iris.cls("Grongier.PEX.Director").dispatchCreateBusinessService(target)
        return iris_object

    @staticmethod
    def create_python_business_service(target):
        """ The create_business_service() method initiates the specified business service.

        Parameters:
        connection: an IRISConnection object that specifies the connection to an IRIS instance for Java.
        target: a string that specifies the name of the business service in the production definition.

        Returns:
            an object that contains an instance of IRISBusinessService
        """
        iris_object = iris.cls("Grongier.PEX.Director").dispatchCreateBusinessService(target)
        return iris_object.GetClass()