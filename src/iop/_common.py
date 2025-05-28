import abc
import inspect
import traceback
from typing import Any, ClassVar, List, Optional, Tuple

from . import _iris
from ._log_manager import LogManager, logging
from ._debugpy import debugpython

class _Common(metaclass=abc.ABCMeta):
    """Base class that defines common methods for all component types.
    
    Provides core functionality like initialization, teardown, connection handling
    and message type checking that is shared across component types.
    """

    INFO_URL: ClassVar[str]
    ICON_URL: ClassVar[str]
    iris_handle: Any = None
    _log_to_console: bool = False
    _logger: Optional[logging.Logger] = None

    @staticmethod
    def get_adapter_type() -> Optional[str]:
        """Get the adapter type for this component. Override in subclasses."""
        return None

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = LogManager.get_logger(self.__class__.__name__,self.log_to_console)
        return self._logger
    
    @logger.setter
    def logger(self, value: logging.Logger) -> None:
        self._logger = value

    @property
    def log_to_console(self) -> bool:
        return self._log_to_console
    
    @log_to_console.setter
    def log_to_console(self, value: bool) -> None:
        self._log_to_console = value
        self.logger = LogManager.get_logger(self.__class__.__name__,value)

    # Lifecycle methods
    def on_init(self) -> None:
        """Initialize component when started."""
        pass

    def on_tear_down(self) -> None:
        """Clean up component before termination."""
        pass

    def on_connected(self) -> None:
        """Handle component connection/reconnection."""
        pass

    # Internal dispatch methods 
    def _dispatch_on_connected(self, host_object: Any) -> None:
        self.on_connected()

    def _dispatch_on_init(self, host_object: Any) -> None:
        """Initialize component when started."""
        self.on_init()

    def _dispatch_on_tear_down(self, host_object: Any) -> None:
        self.on_tear_down()

    def _set_iris_handles(self, handle_current: Any, handle_partner: Any) -> None:
        """Internal method to set IRIS handles."""
        pass

    def _debugpy(self, host) -> None:
        """Set up debugpy for debugging."""
        if debugpython is not None:
            debugpython(self=self, host_object=host)

    # Component information methods
    @classmethod
    def _get_info(cls) -> List[str]:
        """Get component configuration information.
        
        Returns information used to display in Production config UI including:
        - Superclass
        - Description  
        - InfoURL
        - IconURL
        - Adapter type (for Business Services/Operations)
        """
        ret = []
        desc = ""
        info_url = ""
        icon_url = ""
        super_class = ""
        adapter = ""
        try:
            # Get tuple of the class's base classes and loop through them until we find one of the PEX component classes
            classes = inspect.getmro(cls)
            for cl in classes:
                classname = str(cl)[7:-1]
                if classname in ["'iop.BusinessService'","'iop.BusinessOperation'","'iop.DuplexOperation'","'iop.DuplexService'",
                                 "'grongier.pex.BusinessService'","'grongier.pex.BusinessOperation'","'grongier.pex.DuplexOperation'","'grongier.pex.DuplexService'"] :
                    # Remove the apostrophes and set as super_class, then find if it uses an adapter
                    super_class = classname[1:-1]
                    adapter = cls.get_adapter_type()
                    if adapter is None:
                        # for retro-compatibility
                        adapter = cls.getAdapterType() # type: ignore
                    break
                elif classname in ["'iop.BusinessProcess'","'iop.DuplexProcess'","'iop.InboundAdapter'","'iop.OutboundAdapter'",
                                   "'grongier.pex.BusinessProcess'","'grongier.pex.DuplexProcess'","'grongier.pex.InboundAdapter'","'grongier.pex.OutboundAdapter'"] :
                    # Remove the apostrophes and set as super_class
                    super_class = classname[1:-1]
                    break

            if ""==super_class:
                return []
            ret.append(super_class)

            # Get the class documentation, if any
            class_desc = inspect.getdoc(cls)
            super_desc = inspect.getdoc(classes[1])
            if class_desc!=super_desc:
                desc = class_desc
            ret.append(str(desc))

            info_url = inspect.getattr_static(cls,"INFO_URL","")
            icon_url = inspect.getattr_static(cls,"ICON_URL","")

            ret.append(info_url)
            ret.append(icon_url)
            
            if ""!=adapter:
                ret.append(adapter)
        except Exception as e:
            raise e
        return ret

    @classmethod 
    def _get_properties(cls) -> List[List[Any]]:
        """Get component properties for Production configuration.
        
        Returns list of property definitions containing:
        - Property name
        - Data type
        - Default value 
        - Required flag
        - Category
        - Description
        
        Only includes non-private class attributes and properties.
        """
        ret = []
        try:
            # getmembers() returns all the members of an obj
            for member in inspect.getmembers(cls):
                # remove private and protected functions
                if not member[0].startswith('_'):
                    # remove other methods and functions
                    if not inspect.ismethod(member[1]) and not inspect.isfunction(member[1]) and not inspect.isclass(member[1]):
                        if member[0] not in ('INFO_URL','ICON_URL','PERSISTENT_PROPERTY_LIST'
                                             ,'log_to_console','logger','iris_handle'
                                             ,'DISPATCH','adapter','Adapter','buffer'
                                             ,'BusinessHost','business_host','business_host_python'):
                            name = member[0]
                            req = 0
                            cat = "Additional"
                            desc = ""
                            # get value, set to "" if None or a @property
                            val = member[1]
                            if isinstance(val,property) or (val is None):
                                val = ""
                            dt = str(type(val))[8:-2]
                            # get datatype from attribute definition, default to String
                            data_type = {'int':'Integer','float':'Numeric','complex':'Numeric','bool':'Boolean'}.get(dt,'String')
                            # if the user has created a attr_info function, then check the annotation on the return from that for more information about this attribute
                            if hasattr(cls,name + '_info') :
                                func = getattr(cls,name+'_info')
                                if callable(func) :
                                    annotations = func.__annotations__['return']
                                    if annotations is not None:
                                        if bool(annotations.get("ExcludeFromSettings")) :
                                            # don't add this attribute to the settings list
                                            continue
                                        req = bool(annotations.get("IsRequired"))
                                        cat = annotations.get("Category","Additional")
                                        desc = annotations.get("Description")
                                        dt = annotations.get("DataType")
                                        # only override DataType found 
                                        if (dt is not None) and ("" != dt):
                                            data_type = {int:'Integer',float:'Number',complex:'Number',bool:'Boolean',str:'String'}.get(dt,str(dt))
                                    default = func()
                                    if default is not None:
                                        val = default
                            # create list of information for this specific property
                            info = []
                            info.append(name)    # Name        
                            info.append(data_type) # DataType
                            info.append(val)  # Default Value
                            info.append(req) # Required
                            info.append(cat) # Category
                            info.append(desc) # Description
                            # add this property to the list
                            ret.append(info)
        except:
            pass
        return ret

    # Logging methods
    def _log(self) -> Tuple[str, Optional[str]]:
        """Get class and method name for logging.
        
        Returns:
            Tuple of (class_name, method_name)
        """
        current_class = self.__class__.__name__
        current_method = None
        try:
            frame = traceback.extract_stack()[-4]
            current_method = frame.name
        except:
            pass
        return current_class, current_method

    def _logging(self, message: str, level: int, to_console: Optional[bool] = None) -> None:
        """Write log entry.
        
        Args:
            message: Message to log
            level: Log level
            to_console: If True, log to console instead of IRIS
        """
        current_class, current_method = self._log()
        if to_console is None:
            to_console = self.log_to_console
        if level == logging.DEBUG:
            self.logger.debug(message, extra={'to_console': to_console, 'class_name': current_class, 'method_name': current_method})
        elif level == logging.INFO:
            self.logger.info(message, extra={'to_console': to_console, 'class_name': current_class, 'method_name': current_method})
        elif level == logging.CRITICAL:
            self.logger.critical(message, extra={'to_console': to_console, 'class_name': current_class, 'method_name': current_method})
        elif level == logging.WARNING:
            self.logger.warning(message, extra={'to_console': to_console, 'class_name': current_class, 'method_name': current_method})
        elif level == logging.ERROR:
            self.logger.error(message, extra={'to_console': to_console, 'class_name': current_class, 'method_name': current_method})

    def trace(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write trace log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.DEBUG, to_console)

    def log_info(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write info log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.INFO, to_console)

    def log_alert(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write alert log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.CRITICAL, to_console)

    def log_warning(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write warning log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.WARNING, to_console)

    def log_error(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write error log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.ERROR, to_console)

    def log_assert(self, message: str) -> None:
        """Write a log entry of type "assert". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        iris = _iris.get_iris()
        current_class, current_method = self._log()
        iris.cls("Ens.Util.Log").LogAssert(current_class, current_method, message)

    def LOGINFO(self, message: str) -> None:
        """DEPRECATED: Use log_info."""
        return self.log_info(message=message)

    def LOGALERT(self, message: str) -> None:
        """DEPRECATED: Use log_alert."""
        return self.log_alert(message)

    def LOGWARNING(self, message: str) -> None:
        """DEPRECATED: Use log_warning."""
        return self.log_warning(message)

    def LOGERROR(self, message: str) -> None:
        """DEPRECATED: Use log_error."""
        return self.log_error(message)

    def LOGASSERT(self, message: str) -> None:
        """DEPRECATED: Use log_assert."""
        return self.log_assert(message)
        
    def OnInit(self) -> None:
        """DEPRECATED: Use on_init."""
        return 

    def OnTearDown(self) -> None:
        """DEPRECATED: Use on_tear_down."""
        return 

    def OnConnected(self) -> None:
        """DEPRECATED: Use on_connected."""
        return