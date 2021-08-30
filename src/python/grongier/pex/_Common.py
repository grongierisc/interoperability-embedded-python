import traceback
import sys
import inspect
import iris

class _Common():
    """ This is a common superclass for all component types that defines common methods."""

    INFO_URL: str
    ICON_URL: str

    def __init__(self):
        self.irisHandle = None
    
    def _setIrisHandles(self, handleCurrent, handlePartner):
        pass

    @classmethod
    def _is_message_instance(cls, object):
        return cls._is_message_class(type(object))

    @classmethod
    def _is_message_class(cls, klass):
        name = klass.__module__ + '.' + klass.__qualname__
        if name == "grongier.pex.Message": return True
        for c in klass.__bases__:
            if cls._is_message_class(c): return True
        return False

    @classmethod
    def _getInfo(cls):
        """ Get class information to display in the Informational Settings expando for Production config items of this Business Host or Adapter.
        This method returns a list of Superclass, Description, InfoURL, and IconURL, and possibly Adapter (if class is a Business Service or Business Operation)
        IconURL is not yet displayed anywhere
        """
        ret = []
        desc = ""
        infoURL = ""
        iconURL = ""
        superClass = ""
        adapter = ""
        try:
            # Get tuple of the class's base classes and loop through them until we find one of the PEX component classes
            classes = inspect.getmro(cls)
            for cl in classes:
                clName = str(cl)[7:-1]
                if clName in ["'grongier.pex.BusinessService'","'grongier.pex.BusinessOperation'"] :
                    # Remove the apostrophes and set as superClass, then find if it uses an adapter
                    superClass = clName[1:-1]
                    adapter = cls.getAdapterType()
                    break
                elif clName in ["'grongier.pex.BusinessProcess'","'grongier.pex.InboundAdapter'","'grongier.pex.OutboundAdapter'"] :
                    # Remove the apostrophes and set as superClass
                    superClass = clName[1:-1]
                    break

            if ""==superClass:
                return ""
            ret.append(superClass)

            # Get the class documentation, if any
            clsDesc = inspect.getdoc(cls)
            superDesc = inspect.getdoc(classes[1])
            if clsDesc!=superDesc:
                desc = clsDesc
            ret.append(str(desc))

            infoURL = inspect.getattr_static(cls,"INFO_URL","")
            iconURL = inspect.getattr_static(cls,"ICON_URL","")

            ret.append(infoURL)
            ret.append(iconURL)
            
            if ""!=adapter:
                ret.append(adapter)
        except:
            pass
        return ret

    @classmethod
    def _getProperties(cls):
        """ Get a list of the Attributes and Properties of this Python class.
        Return value is a list of lists of form $lb(propName,dataType,defaultVal,required,category,description).
        which can be used by the Production Configuration to display them as settings.
        This list will only include class attributes (no instance attributes) and properties which are not marked to be private by use of the _ prefix.
        For class attributes, we will use the value that it is defined with as the defaultVal and its type as the dataType, or "" and String if set to None.
        Add a function attrName_info() for a attribute or property 'attrName' in order to add more information about that attribute by using the function annotation for the return value.
        The annotation should be a dictionary including any of 'IsRequired', 'Category', 'Description', 'DataType', or 'ExcludeFromSettings' as keys.
        'ExcludeFromSettings' should be a boolean, and if true will exclude an attribute from being returned in the list, and so prevent it from being displayed as a setting in the Production Configuration Page
        'DataType' does not need to be specified if it is the same as the type of the attribute definition.  Otherwise, it can be either a Python type or a string.
        If 'IsRequired' is not specified, this will default to false.
        If 'Category' is not specified, the attribute will be added to the Additional category.
        """
        ret = []
        try:
            # getmembers() returns all the members of an object
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
                            dataType = {'int':'Integer','float':'Numeric','complex':'Numeric','bool':'Boolean'}.get(dt,'String')
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
                                            dataType = {int:'Integer',float:'Number',complex:'Number',bool:'Boolean',str:'String'}.get(dt,str(dt))
                                    default = func()
                                    if default is not None:
                                        val = default
                            # create list of information for this specific property
                            info = []
                            info.append(name)    # Name        
                            info.append(dataType) # DataType
                            info.append(val)  # Default Value
                            info.append(req) # Required
                            info.append(cat) # Category
                            info.append(desc) # Description
                            # add this property to the list
                            ret.append(info)
        except:
            pass
        return ret

    def LOGINFO(self, message):
        """ Write a log entry of type "info". :og entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """

        currentClass = self.__class__.__name__
        currentMethod = None
        try:
            frame = traceback.extract_stack()[-2]
            currentMethod = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogInfo(currentClass, currentMethod, message)
        return

    def LOGALERT(self, message):
        """ Write a log entry of type "alert". :og entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        currentClass = self.__class__.__name__
        currentMethod = None
        try:
            frame = traceback.extract_stack()[-2]
            currentMethod = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogAlert(currentClass, currentMethod, message)
        return

    def LOGWARNING(self, message):
        """ Write a log entry of type "warning". Log entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        currentClass = self.__class__.__name__
        currentMethod = None
        try:
            frame = traceback.extract_stack()[-2]
            currentMethod = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogWarning(currentClass, currentMethod, message)
        return

    def LOGERROR(self, message):
        """ Write a log entry of type "error". :og entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        currentClass = self.__class__.__name__
        currentMethod = None
        try:
            frame = traceback.extract_stack()[-2]
            currentMethod = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogError(currentClass, currentMethod, message)
        return

    def LOGASSERT(self, message):
        """ Write a log entry of type "assert". :og entries can be viewed in the management portal.
        
        Parameters:
        message: a string that is written to the log.
        """
        currentClass = self.__class__.__name__
        currentMethod = None
        try:
            frame = traceback.extract_stack()[-2]
            currentMethod = frame.name
        except:
            pass
        iris.cls("Ens.Util.Log").LogAssert(currentClass, currentMethod, message)
        return

        