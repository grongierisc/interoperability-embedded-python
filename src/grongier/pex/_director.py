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
    
    ### List of function to manage the production
    ### start production
    @staticmethod
    def start_production(production_name):
        pass

    ### stop production
    @staticmethod
    def stop_production(production_name):
        pass

    ### restart production
    @staticmethod
    def restart_production(production_name):
        pass

    ### shutdown production
    @staticmethod
    def shutdown_production(production_name):
        pass

    ### update production
    @staticmethod
    def update_production(production_name):
        pass

    ### list production
    @staticmethod
    def list_production():
        pass