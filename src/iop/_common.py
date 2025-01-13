import abc
import dataclasses
import inspect
import iris
import traceback
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type
from iop._log_manager import LogManager
import logging

class _Common(metaclass=abc.ABCMeta):
    """Base class that defines common methods for all component types.
    
    Provides core functionality like initialization, teardown, connection handling
    and message type checking that is shared across component types.
    """

    INFO_URL: ClassVar[str]
    ICON_URL: ClassVar[str]
    iris_handle: Any = None
    log_to_console: bool = False

    def on_init(self) -> None:
        """Initialize component when started.
        
        Called when component starts. Use to initialize required structures.
        """
        return self.OnInit()

    def on_tear_down(self) -> None:
        """Clean up component before termination.
        
        Called before component terminates. Use to free resources.
        """
        return self.OnTearDown()

    def on_connected(self) -> None:
        """Handle component connection/reconnection.
        
        Called when component connects or reconnects after disconnection.
        Use to initialize connection-dependent structures.
        """
        return self.OnConnected()

    def _dispatch_on_connected(self, host_object: Any) -> None:
        """Internal dispatch for connection handling."""
        self.on_connected()
        return

    def _dispatch_on_init(self, host_object: Any) -> None:
        """Internal dispatch for initialization."""
        self.on_init()
        return

    def _dispatch_on_tear_down(self, host_object: Any) -> None:
        """Internal dispatch for teardown."""
        self.on_tear_down()
        return

    def _set_iris_handles(self, handle_current: Any, handle_partner: Any) -> None:
        """Internal method to set IRIS handles."""
        pass

    @classmethod
    def _is_message_instance(cls, obj: Any) -> bool:
        """Check if object is a valid Message instance.
        
        Args:
            obj: Object to check
            
        Returns:
            True if object is a Message instance
            
        Raises:
            TypeError: If object is Message class but not a dataclass
        """
        if cls._is_message_class(type(obj)):
            if not dataclasses.is_dataclass(obj):
                raise TypeError(f"{type(obj).__module__}.{type(obj).__qualname__} must be a dataclass")
            return True
        return False

    @classmethod
    def _is_pickle_message_instance(cls, obj: Any) -> bool:
        """Check if object is a PickleMessage instance."""
        if cls._is_pickel_message_class(type(obj)):
            return True
        return False
    
    @classmethod
    def _is_iris_object_instance(cls, obj: Any) -> bool:
        """Check if object is an IRIS persistent object."""
        if (obj is not None and type(obj).__module__.find('iris') == 0) and obj._IsA("%Persistent"):
            return True
        return False

    @classmethod
    def _is_message_class(cls, klass: Type) -> bool:
        name = klass.__module__ + '.' + klass.__qualname__
        if name == "iop.Message" or name == "grongier.pex.Message": 
            return True
        for c in klass.__bases__:
            if cls._is_message_class(c): 
                return True
        return False

    @classmethod
    def _is_pickel_message_class(cls, klass: Type) -> bool:
        name = klass.__module__ + '.' + klass.__qualname__
        if name == "iop.PickleMessage" or name == "grongier.pex.PickleMessage": 
            return True
        for c in klass.__bases__:
            if cls._is_pickel_message_class(c): 
                return True
        return False

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
                        adapter = cls.getAdapterType()
                    break
                elif classname in ["'iop.BusinessProcess'","'iop.DuplexProcess'","'iop.InboundAdapter'","'iop.OutboundAdapter'",
                                   "'grongier.pex.BusinessProcess'","'grongier.pex.DuplexProcess'","'grongier.pex.InboundAdapter'","'grongier.pex.OutboundAdapter'"] :
                    # Remove the apostrophes and set as super_class
                    super_class = classname[1:-1]
                    break

            if ""==super_class:
                return ""
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
                        if member[0] not in ('INFO_URL','ICON_URL','PERSISTENT_PROPERTY_LIST') :
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

    @property
    def logger(self) -> logging.Logger:
        """Get a logger instance for this component.
        
        Returns:
            Logger configured for IRIS integration
        """
        class_name, method_name = self._log()
        return LogManager.get_logger(class_name, method_name, self.log_to_console)

    def trace(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write trace log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self.logger.debug(message, extra={'to_console': to_console})


    def log_info(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write info log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self.logger.info(message, extra={'to_console': to_console})

    def log_alert(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write alert log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self.logger.critical(message, extra={'to_console': to_console})

    def log_warning(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write warning log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self.logger.warning(message, extra={'to_console': to_console})

    def log_error(self, message: str, to_console: Optional[bool] = None) -> None:
        """Write error log entry.
        
        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self.logger.error(message, extra={'to_console': to_console})

    def log_assert(self, message: str) -> None:
        """Write a log entry of type "assert". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
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