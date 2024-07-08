import traceback
import dataclasses
import inspect
import iris
import abc

class _Common(metaclass=abc.ABCMeta):
    """ This is a common superclass for all component types that defines common methods."""

    INFO_URL: str
    ICON_URL: str
    iris_handle = None

    def on_init(self):
        """ The on_init() method is called when the component is started.
        Use the on_init() method to initialize any structures needed by the component."""
        return self.OnInit()

    def on_tear_down(self):
        """ Called before the component is terminated. Use it to free any structures."""
        return self.OnTearDown()

    def on_connected(self):
        """ The on_connected() method is called when the component is connected or reconnected after being disconnected.
        Use the on_connected() method to initialize any structures needed by the component."""
        return self.OnConnected()

    def _dispatch_on_connected(self, host_object):
        """ For internal use only. """
        self.on_connected()
        return

    def _dispatch_on_init(self, host_object):
        """ For internal use only. """
        self.on_init()
        return

    def _dispatch_on_tear_down(self, host_object):
        """ For internal use only. """
        self.on_tear_down()
        return

    def _set_iris_handles(self, handle_current, handle_partner):
        pass

    @classmethod
    def _is_message_instance(cls, obj):
        if cls._is_message_class(type(obj)):
            if not dataclasses.is_dataclass(obj):
                raise TypeError(type(obj).__module__ + '.' + type(obj).__qualname__+" must be a dataclass")
            return True
        return False

    @classmethod
    def _is_pickle_message_instance(cls, obj):
        if cls._is_pickel_message_class(type(obj)):
            return True
        return False
    
    @classmethod
    def _is_iris_object_instance(cls, obj):
        if (obj is not None and type(obj).__module__.find('iris') == 0) and obj._IsA("%Persistent"):
            return True
        return False

    @classmethod
    def _is_message_class(cls, klass):
        name = klass.__module__ + '.' + klass.__qualname__
        if name == "iop.Message" or name == "grongier.pex.Message": 
            return True
        for c in klass.__bases__:
            if cls._is_message_class(c): 
                return True
        return False

    @classmethod
    def _is_pickel_message_class(cls, klass):
        name = klass.__module__ + '.' + klass.__qualname__
        if name == "iop.PickleMessage" or name == "grongier.pex.PickleMessage": 
            return True
        for c in klass.__bases__:
            if cls._is_pickel_message_class(c): 
                return True
        return False

    @classmethod
    def _get_info(cls):
        """ Get class information to display in the Informational Settings expando for Production config items of this Business Host or Adapter.
        This method returns a list of Superclass, Description, InfoURL, and IconURL, and possibly Adapter (if class is a Business Service or Business Operation)
        IconURL is not yet displayed anywhere
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
    def _get_properties(cls):
        """ Get a list of the Attributes and Properties of this Python class.
        Return value is a list of lists of form $lb(propName,data_type,defaultVal,required,category,description).
        which can be used by the Production Configuration to display them as settings.
        This list will only include class attributes (no instance attributes) and properties which are not marked to be private by use of the _ prefix.
        For class attributes, we will use the value that it is defined with as the defaultVal and its type as the data_type, or "" and String if set to None.
        Add a function attrName_info() for a attribute or property 'attrName' in order to add more information about that attribute by using the function annotation for the return value.
        The annotation should be a dictionary including any of 'IsRequired', 'Category', 'Description', 'DataType', or 'ExcludeFromSettings' as keys.
        'ExcludeFromSettings' should be a boolean, and if true will exclude an attribute from being returned in the list, and so prevent it from being displayed as a setting in the Production Configuration Page
        'DataType' does not need to be specified if it is the same as the type of the attribute definition.  Otherwise, it can be either a Python type or a string.
        If 'IsRequired' is not specified, this will default to false.
        If 'Category' is not specified, the attribute will be added to the Additional category.
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

    def log_info(self, message):
        """ Write a log entry of type "info". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """

        current_class = self.__class__.__name__
        current_method = None
        try:
            frame = traceback.extract_stack()[-2]
            current_method = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogInfo(current_class, current_method, message)
        return

    def log_alert(self, message):
        """ Write a log entry of type "alert". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        current_class = self.__class__.__name__
        current_method = None
        try:
            frame = traceback.extract_stack()[-2]
            current_method = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogAlert(current_class, current_method, message)
        return

    def log_warning(self, message):
        """ Write a log entry of type "warning". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        current_class = self.__class__.__name__
        current_method = None
        try:
            frame = traceback.extract_stack()[-2]
            current_method = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogWarning(current_class, current_method, message)
        return

    def log_error(self, message):
        """ Write a log entry of type "error". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        current_class = self.__class__.__name__
        current_method = None
        try:
            frame = traceback.extract_stack()[-2]
            current_method = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogError(current_class, current_method, message)
        return

    def log_assert(self, message):
        """ Write a log entry of type "assert". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        current_class = self.__class__.__name__
        current_method = None
        try:
            frame = traceback.extract_stack()[-2]
            current_method = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogAssert(current_class, current_method, message)
        return

    def LOGINFO(self, message):
        """ DECAPRETED : use log_info
        Write a log entry of type "info". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        return self.log_info(message=message)

    def LOGALERT(self, message):
        """ DECAPRETED : use log_alert
        Write a log entry of type "alert". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        return self.log_alert(message)

    def LOGWARNING(self, message):
        """ DECAPRETED : use log_warning
        Write a log entry of type "warning". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        return self.log_warning(message)

    def LOGERROR(self, message):
        """ DECAPRETED : use log_error
        Write a log entry of type "error". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        return self.log_error(message)

    def LOGASSERT(self, message):
        """ DECAPRETED : use log_assert
        Write a log entry of type "assert". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        return self.log_assert(message)
        
    def OnInit(self):
        """ DEPRECATED : use on_init
        The on_init() method is called when the component is started.
        Use the on_init() method to initialize any structures needed by the component."""
        return 

    def OnTearDown(self):
        """ DEPRECATED : use on_tear_down
        Called before the component is terminated. Use it to freee any structures.
        """
        return 

    def OnConnected(self):
        """ DEPRECATED : use on_connected
        The on_connected() method is called when the component is connected or reconnected after being disconnected.
        Use the on_connected() method to initialize any structures needed by the component."""
        return 