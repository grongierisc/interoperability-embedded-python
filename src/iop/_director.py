import asyncio
import datetime
import functools
import signal
from dataclasses import dataclass

from . import _iris
from ._dispatch import dispatch_deserializer, dispatch_serializer
from ._utils import _Utils

@dataclass
class SigintHandler():
    
    sigint: bool = False
    sigint_log: bool = False
    log_only: bool = False

    def signal_handler(self, signal, frame):
        if self.sigint or self.log_only:
            self.sigint_log = True
        self.sigint = True

class _Director():
    """ The Directorclass is used for nonpolling business services, that is, business services which are not automatically
    called by the production framework (through the inbound adapter) at the call interval.
    Instead these business services are created by a custom application by calling the Director.CreateBusinessService() method.
    """

    _bs = {}

    def get_business_service(self,target,force_session_id=False):
        """ get the business service
        Parameters:
        target: the name of the business service
        force_session_id: if True, force the session id to be a new one
        """
        if target not in self._bs or self._bs[target] is None:
            self._bs[target] = _Director.create_python_business_service(target)
        if force_session_id:
            self._bs[target].iris_handle._SessionId = ""
            self._bs[target].iris_handle.ForceSessionId()
        return self._bs[target]

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
        iris_object = _iris.get_iris().cls("IOP.Director").dispatchCreateBusinessService(target)
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
        iris_object = _iris.get_iris().cls("IOP.Director").dispatchCreateBusinessService(target)
        return iris_object.GetClass()
    
    ### List of function to manage the production
    ### start production
    @staticmethod
    def start_production_with_log(production_name=None):
        if production_name is None or production_name == '':
            production_name = _Director.get_default_production()
        # create two async task
        loop = asyncio.get_event_loop()
        # add signal handler
        handler = SigintHandler()
        loop.add_signal_handler(signal.SIGINT, functools.partial(handler.signal_handler, signal.SIGINT, loop))
        loop.run_until_complete(asyncio.gather(
            _Director._start_production_async(production_name, handler),
            _Director._log_production_async(handler)
        ))
        loop.close()

    @staticmethod
    async def _start_production_async(production_name:str, handler: SigintHandler):
        _Director.start_production(production_name)
        while True:
            if handler.sigint:
                _Director.stop_production()
                break
            await asyncio.sleep(1)

    @staticmethod
    def start_production(production_name=None):
        if production_name is None or production_name == '':
            production_name = _Director.get_default_production()
        _iris.get_iris().cls('Ens.Director').StartProduction(production_name)

    ### stop production
    @staticmethod
    def stop_production():
        _iris.get_iris().cls('Ens.Director').StopProduction()

    ### restart production
    @staticmethod
    def restart_production():
        _iris.get_iris().cls('Ens.Director').RestartProduction()

    ### shutdown production
    @staticmethod
    def shutdown_production():
        _iris.get_iris().cls('Ens.Director').StopProduction(10,1)

    ### update production
    @staticmethod
    def update_production():
        _iris.get_iris().cls('Ens.Director').UpdateProduction()

    ### list production
    @staticmethod
    def list_productions():
        return _iris.get_iris().cls('IOP.Director').dispatchListProductions()
    
    ### status production
    @staticmethod
    def status_production():
        dikt = _iris.get_iris().cls('IOP.Director').StatusProduction()
        if dikt['Production'] is None or dikt['Production'] == '':
            dikt['Production'] = _Director.get_default_production()
        return dikt

    ### set default production
    @staticmethod
    def set_default_production(production_name=''):
        #set ^Ens.Configuration("SuperUser","LastProduction")
        glb = _iris.get_iris().gref("^Ens.Configuration")
        glb['csp', "LastProduction"] = production_name

    ### get default production
    @staticmethod
    def get_default_production():
        glb = _iris.get_iris().gref("^Ens.Configuration")
        default_production_name = glb['csp', "LastProduction"]
        if default_production_name is None or default_production_name == '':
            default_production_name = 'Not defined'
        return default_production_name

    @staticmethod
    def format_log(row: list) -> str:
        # 0,  1,          2,   3,         4,         5,           6,            7,     8,    9,          10,        11
        # ID, ConfigName, Job, MessageId, SessionId, SourceClass, SourceMethod, Stack, Text, TimeLogged, TraceCat, Type
        # yield all except stack aand tracecat
        # in first position, the timelogged
        # cast the result to string
        # convert Type to its string value
            # Assert,Error,Warning,Info,Trace,Alert
        typ = row[11]
        if typ == 1:
            typ = 'Assert'
        elif typ == 2:
            typ = 'Error'
        elif typ == 3:
            typ = 'Warning'
        elif typ == 4:
            typ = 'Info'
        elif typ == 5:
            typ = 'Trace'
        elif typ == 6:
            typ = 'Alert'
        return str(row[9]) + ' ' + typ + ' ' + str(row[1]) + ' ' + str(row[2]) + ' ' + str(row[3]) + ' ' + str(row[4]) + ' ' + str(row[5]) + ' ' + str(row[6]) + ' ' + str(row[8])

    @staticmethod
    def read_top_log(top) -> list:
        sql = """
        SELECT top ?
        ID, ConfigName, Job, MessageId, SessionId, SourceClass, SourceMethod, Stack, Text, TimeLogged, TraceCat, Type
        FROM Ens_Util.Log
        order by id desc
        """
        result = []
        stmt = _iris.get_iris().sql.prepare(sql)
        rs = stmt.execute(top)
        for row in rs:
            result.append(_Director.format_log(row))
        return result

    @staticmethod
    def read_log() -> list:
        sql = """
        SELECT 
        ID, ConfigName, Job, MessageId, SessionId, SourceClass, SourceMethod, Stack, Text, TimeLogged, TraceCat, Type
        FROM Ens_Util.Log
        where TimeLogged >= ?
        order by id desc
        """
        result = []
        stmt = _iris.get_iris().sql.prepare(sql)
        time = datetime.datetime.now() - datetime.timedelta(seconds=1)
        # convert to utc time
        time = time.astimezone(datetime.timezone.utc)
        rs = stmt.execute(time.isoformat(sep=' '))
        for row in rs:
            result.append(_Director.format_log(row))
        return result

    @staticmethod
    async def _log_production_async(handler):
        """ Log production 
            if ctrl+c is pressed, the log is stopped
        """
        while True:
            for row in reversed(_Director.read_log()):
                print(row)
            if handler.sigint_log:
                break
            await asyncio.sleep(1)

    @staticmethod
    def log_production_top(top=10):
        """ 
        Log the top N logs of the production
        Parameters:
        top: the number of log to display
        """
        for row in reversed(_Director.read_top_log(top)):
            print(row)

    @staticmethod
    def log_production():
        """ Log production 
            if ctrl+c is pressed, the log is stopped
        """
        loop = asyncio.get_event_loop()
        handler = SigintHandler(log_only=True)
        loop.add_signal_handler(signal.SIGINT, functools.partial(handler.signal_handler, signal.SIGINT, loop))

        for row in reversed(_Director.read_top_log( 10)):
            print(row)
    
        loop.run_until_complete(_Director._log_production_async(handler))
        loop.close()

    @staticmethod
    def test_component(target,message=None,classname=None,body=None):
        """ 
        Test a component
        Parameters:
        target: the name of the component
        classname: the name of the class to test
        body: the body of the message
        """
        if not message:
            message = _iris.get_iris().cls('Ens.Request')._New()
        if classname:
            # if classname start with 'iris.' then create an iris object
            if classname.startswith('iris.'):
                # strip the iris. prefix
                classname = classname[5:]
                if body:
                    message = _iris.get_iris().cls(classname)._New(body)
                else:
                    message = _iris.get_iris().cls(classname)._New()
            # else create a python object
            else:
                # python message are casted to Grongier.PEX.Message
                message = _iris.get_iris().cls("IOP.Message")._New()
                message.classname = classname
                if body:
                    message.json = body
                else:
                    message.json = _Utils.string_to_stream("{}")
        # serialize the message
        serial_message = dispatch_serializer(message)
        response = _iris.get_iris().cls('IOP.Utils').dispatchTestComponent(target,serial_message)
        try:
            deserialized_response = dispatch_deserializer(response)
        except ImportError as e:
            # can't import the class, return the string
            deserialized_response = f'{response.classname} : {_Utils.stream_to_string(response.jstr)}'
        return deserialized_response

