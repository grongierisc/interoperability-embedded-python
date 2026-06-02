"""Local IRIS director functions and deprecated _Director facade."""

import asyncio
import datetime
import functools
import signal
import warnings
from dataclasses import dataclass
from functools import wraps

from ..messages.dispatch import dispatch_deserializer, dispatch_serializer
from ..migration import utils as _migration_utils
from ..runtime import iris as _iris


@dataclass
class SigintHandler:
    sigint: bool = False
    sigint_log: bool = False
    log_only: bool = False

    def signal_handler(self, signal, frame):
        if self.sigint or self.log_only:
            self.sigint_log = True
        self.sigint = True


def create_business_service(target):
    """The create_business_service() method initiates the specified business service.

    Parameters:
    connection: an IRISConnection object that specifies the connection to an IRIS instance for Java.
    target: a string that specifies the name of the business service in the production definition.

    Returns:
        an object that contains an instance of IRISBusinessService
    """
    iris_object = (
        _iris.get_iris().cls("IOP.Director").dispatchCreateBusinessService(target)
    )
    return iris_object


def create_python_business_service(target):
    """The create_business_service() method initiates the specified business service.

    Parameters:
    connection: an IRISConnection object that specifies the connection to an IRIS instance for Java.
    target: a string that specifies the name of the business service in the production definition.

    Returns:
        an object that contains an instance of IRISBusinessService
    """
    iris_object = (
        _iris.get_iris().cls("IOP.Director").dispatchCreateBusinessService(target)
    )
    return iris_object.GetClass()


### List of function to manage the production
### start production
def start_production_with_log(production_name=None):
    if production_name is None or production_name == "":
        production_name = get_default_production()
    # create two async task
    loop = asyncio.get_event_loop()
    # add signal handler
    handler = SigintHandler()
    loop.add_signal_handler(
        signal.SIGINT,
        functools.partial(handler.signal_handler, signal.SIGINT, loop),
    )
    loop.run_until_complete(
        asyncio.gather(
            _start_production_async(production_name, handler),
            _log_production_async(handler),
        )
    )
    loop.close()


async def _start_production_async(production_name: str, handler: SigintHandler):
    start_production(production_name)
    while True:
        if handler.sigint:
            stop_production()
            break
        await asyncio.sleep(1)


def start_production(production_name=None):
    if production_name is None or production_name == "":
        production_name = get_default_production()
    status = _iris.get_iris().cls("Ens.Director").StartProduction(production_name)
    _migration_utils.raise_on_error(status)


### stop production
def stop_production():
    _iris.get_iris().cls("Ens.Director").StopProduction()


### restart production
def restart_production():
    _iris.get_iris().cls("Ens.Director").RestartProduction()


### shutdown production
def shutdown_production():
    _iris.get_iris().cls("Ens.Director").StopProduction(10, 1)


### update production
def update_production():
    _iris.get_iris().cls("Ens.Director").UpdateProduction()


### start production component
def start_component(component_name):
    status = (
        _iris.get_iris()
        .cls("Ens.Director")
        .EnableConfigItem(
            component_name,
            1,
            1,
        )
    )
    _migration_utils.raise_on_error(status)


### stop production component
def stop_component(component_name):
    status = (
        _iris.get_iris()
        .cls("Ens.Director")
        .EnableConfigItem(
            component_name,
            0,
            1,
        )
    )
    _migration_utils.raise_on_error(status)


### restart production component
def restart_component(component_name):
    stop_component(component_name)
    start_component(component_name)


### list production
def list_productions():
    return _iris.get_iris().cls("IOP.Director").dispatchListProductions()


### status production
def status_production():
    dikt = _iris.get_iris().cls("IOP.Director").StatusProduction()
    if dikt["Production"] is None or dikt["Production"] == "":
        dikt["Production"] = get_default_production()
    return dikt


### set default production
def set_default_production(production_name=""):
    # set ^Ens.Configuration("SuperUser","LastProduction")
    glb = _iris.get_iris().gref("^Ens.Configuration")
    glb["csp", "LastProduction"] = production_name


### get default production
def get_default_production():
    glb = _iris.get_iris().gref("^Ens.Configuration")
    default_production_name = glb["csp", "LastProduction"]
    if default_production_name is None or default_production_name == "":
        default_production_name = "Not defined"
    return default_production_name


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
        typ = "Assert"
    elif typ == 2:
        typ = "Error"
    elif typ == 3:
        typ = "Warning"
    elif typ == 4:
        typ = "Info"
    elif typ == 5:
        typ = "Trace"
    elif typ == 6:
        typ = "Alert"
    return (
        str(row[9])
        + " "
        + typ
        + " "
        + str(row[1])
        + " "
        + str(row[2])
        + " "
        + str(row[3])
        + " "
        + str(row[4])
        + " "
        + str(row[5])
        + " "
        + str(row[6])
        + " "
        + str(row[8])
    )


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
        result.append(format_log(row))
    return result


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
    rs = stmt.execute(time.isoformat(sep=" "))
    for row in rs:
        result.append(format_log(row))
    return result


async def _log_production_async(handler):
    """Log production
    if ctrl+c is pressed, the log is stopped
    """
    while True:
        for row in reversed(read_log()):
            print(row)
        if handler.sigint_log:
            break
        await asyncio.sleep(1)


def log_production_top(top=10):
    """
    Log the top N logs of the production
    Parameters:
    top: the number of log to display
    """
    for row in reversed(read_top_log(top)):
        print(row)


def log_production():
    """Log production
    if ctrl+c is pressed, the log is stopped
    """
    loop = asyncio.get_event_loop()
    handler = SigintHandler(log_only=True)
    loop.add_signal_handler(
        signal.SIGINT,
        functools.partial(handler.signal_handler, signal.SIGINT, loop),
    )

    for row in reversed(read_top_log(10)):
        print(row)

    loop.run_until_complete(_log_production_async(handler))
    loop.close()


def test_component(target, message=None, classname=None, body=None):
    """
    Test a component
    Parameters:
    target: the name of the component
    classname: the name of the class to test
    body: the body of the message
    """
    iris = _iris.get_iris()
    if not message:
        message = iris.cls("Ens.Request")._New()
    if classname:
        # if classname start with 'iris.' then create an iris object
        if classname.startswith("iris."):
            # strip the iris. prefix
            classname = classname[5:]
            if body:
                message = iris.cls(classname)._New(body)
            else:
                message = iris.cls(classname)._New()
        # else create a python object
        else:
            message = iris.cls("IOP.Message")._New()
            message.classname = classname
            if body:
                message.json = body
            else:
                message.json = _migration_utils.string_to_stream("{}")
    # serialize the message
    serial_message = dispatch_serializer(message)
    response = iris.cls("IOP.Utils").dispatchTestComponent(target, serial_message)
    try:
        deserialized_response = dispatch_deserializer(response)
    except ImportError:
        # can't import the class, return the string
        deserialized_response = (
            f"{response.classname} : {_migration_utils.stream_to_string(response.jstr)}"
        )
    return deserialized_response


def _deprecated_static(name: str):
    target = globals()[name]
    if asyncio.iscoroutinefunction(target):

        @wraps(target)
        async def async_wrapper(*args, **kwargs):
            warnings.warn(
                f"iop.runtime.director._Director.{name}() and iop.Director.{name}() are deprecated; "
                f"use iop.runtime.director.{name}() instead. This facade will be removed in v5.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            return await globals()[name](*args, **kwargs)

        return staticmethod(async_wrapper)

    @wraps(target)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"iop.runtime.director._Director.{name}() and iop.Director.{name}() are deprecated; "
            f"use iop.runtime.director.{name}() instead. This facade will be removed in v5.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return globals()[name](*args, **kwargs)

    return staticmethod(wrapper)


class _Director:
    """Compatibility facade for the local IRIS director API."""

    _bs = {}

    def get_business_service(self, target, force_session_id=False):
        """Get and cache a Python business service by production item name."""
        if target not in self._bs or self._bs[target] is None:
            self._bs[target] = create_python_business_service(target)
        if force_session_id:
            self._bs[target].iris_handle._SessionId = ""
            self._bs[target].iris_handle.ForceSessionId()
        return self._bs[target]

    create_business_service = _deprecated_static("create_business_service")
    create_python_business_service = _deprecated_static(
        "create_python_business_service"
    )
    start_production_with_log = _deprecated_static("start_production_with_log")
    _start_production_async = _deprecated_static("_start_production_async")
    start_production = _deprecated_static("start_production")
    stop_production = _deprecated_static("stop_production")
    restart_production = _deprecated_static("restart_production")
    shutdown_production = _deprecated_static("shutdown_production")
    update_production = _deprecated_static("update_production")
    start_component = _deprecated_static("start_component")
    stop_component = _deprecated_static("stop_component")
    restart_component = _deprecated_static("restart_component")
    list_productions = _deprecated_static("list_productions")
    status_production = _deprecated_static("status_production")
    set_default_production = _deprecated_static("set_default_production")
    get_default_production = _deprecated_static("get_default_production")
    format_log = _deprecated_static("format_log")
    read_top_log = _deprecated_static("read_top_log")
    read_log = _deprecated_static("read_log")
    _log_production_async = _deprecated_static("_log_production_async")
    log_production_top = _deprecated_static("log_production_top")
    log_production = _deprecated_static("log_production")
    test_component = _deprecated_static("test_component")
