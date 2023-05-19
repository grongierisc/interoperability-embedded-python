import iris
import datetime
import time
import intersystems_iris.dbapi._DBAPI as irisdbapi
import signal
import sys
import asyncio

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
    def start_production(production_name=None):
        # create two async task
        loop = asyncio.get_event_loop()
        handler = SIGINT_handler()
        print('start production')
        loop.run_until_complete(asyncio.gather(
            _Director.start_production_async(production_name, handler),
            _Director.log_production(handler)
        ))

    @staticmethod
    async def start_production_async(production_name=None, handler=None):
        signal.signal(signal.SIGINT, handler.signal_handler)
        iris.cls('Ens.Director').StartProduction(production_name)
        while True:
            if handler.SIGINT:
                print('try to stop production')
                _Director.stop_production(production_name)
                print('production stopped')
                break
            await asyncio.sleep(1)

    ### stop production
    @staticmethod
    def stop_production(production_name=None):
        iris.cls('Ens.Director').StopProduction()

    ### restart production
    @staticmethod
    def restart_production(production_name=None):
        iris.cls('Ens.Director').RestartProduction()

    ### shutdown production
    @staticmethod
    def shutdown_production(production_name=None):
        iris.cls('Ens.Director').StopProduction(10,1)

    ### update production
    @staticmethod
    def update_production(production_name=None):
        iris.cls('Ens.Director').UpdateProduction()

    ### list production
    @staticmethod
    def list_productions():
        return iris.cls('Grongier.PEX.Director').dispatchListProductions()

    @staticmethod
    def read_log(handler):
        sql = """
        SELECT 
        ID, ConfigName, Job, MessageId, SessionId, SourceClass, SourceMethod, Stack, Text, TimeLogged, TraceCat, Type
        FROM Ens_Util.Log
        where TimeLogged >= ?
        order by id desc
        """
        signal.signal(signal.SIGINT, handler.signal_handler)
        with irisdbapi.connect(embedded=True) as connection:
            with connection.cursor() as cursor:
                while True:
                    cursor.execute(sql, (datetime.datetime.now() - datetime.timedelta(seconds=1),))
                    for row in cursor:
                        yield f'{row[9]} {row[5]} {row[6]} {row[7]} {row[8]}'
                    time.sleep(1)
                    if handler.SIGINT:
                        break

    @staticmethod
    async def log_production(handler):
        """ Log production 
            if ctrl+c is pressed, the log is stopped
        """
        for line in _Director.read_log(handler):
            print(line)
            sys.stdout.flush()

            

class SIGINT_handler():
    def __init__(self):
        self.SIGINT = False

    def signal_handler(self, signal, frame):
        self.SIGINT = True
