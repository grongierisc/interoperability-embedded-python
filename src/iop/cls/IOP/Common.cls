/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Include Ensemble

Class IOP.Common [ Abstract, ClassType = "", ProcedureBlock, System = 4 ]
{

/// One or more Classpaths (separated by '|' character)
Property %classpaths As %String(MAXLEN = "");

/// Classname of the Python class to use
Property %classname As %String(MAXLEN = "");

/// Module of the Python class to use
Property %module As %String(MAXLEN = "");

/// Settings for the Python class, in the form of "property=value" pairs, separated by newlines
/// Example: "property1=value1\nproperty2=value2"
/// Note: This property is used to set the properties of the Python class dynamically
Property %settings As %String(MAXLEN = "");

/// Instance of class
Property %class As %SYS.Python;

/// Enable debugging
/// If set to 1, the Python class will be debugged using the debugpy module
/// If set to 0, the Python class will not be debugged
Property %enable As %Boolean;

/// Timeout in seconds for the an client debugging connection
Property %timeout As %Numeric [ InitialExpression = 30 ];

/// Port to use for the an client debugging connection
Property %port As %Numeric [ InitialExpression = 0 ];

/// Path to the Python interpreter for debugpy
Property %PythonInterpreterPath As %String(MAXLEN = 255);

/// Enable traceback display
Property %traceback As %Boolean [ InitialExpression = 1 ];

/// Enable virtual environment
Property %Venv As %Boolean [ InitialExpression = 0 ];

/// Virtual environment site-packages path
Property %PythonPath As %String(MAXLEN = 255);

/// Path to the Python runtime library
Property %PythonRuntimeLibrary As %String(MAXLEN = 255);

/// Version of the Python runtime library
Property %PythonRuntimeLibraryVersion As %String;

/// Get Class
Method GetClass() As %SYS.Python
{
    Return ..%class
}

/// Get Classname
Method GetClassname() As %String
{
    Return ..%classname
}

/// Get Classname
Method GetModule() As %String
{
    Return ..%module
}

Method DisplayTraceback(ex) As %Status
{
    set tSC = ex.AsStatus()
    // Check if traceback is enabled
    if ..%traceback {
        // Import Modules
        set sys = ##class(%SYS.Python).Import("sys")
        set tracebackModule = ##class(%SYS.Python).Import("traceback")
        set builtins = ##class(%SYS.Python).Import("builtins")
        // Get the last traceback
        set traceback = sys."last_traceback"
        set exType = sys."last_type"."__name__"
        set exValue = sys."last_value"."__str__"()
        // Check if traceback is an object
        if $isObject(traceback) {
            // Format the traceback
            set tb = tracebackModule."format_exception"(sys."last_type", sys."last_value", traceback)
            set tbString = ""
            for i=0:1:(tb."__len__"()-1) {
                set tbString = tbString _ $c(10)_$c(13) _ tb."__getitem__"(i)
            }
            $$$LOGERROR(tbString)
            set tSC = $$$ERROR($$$EnsErrGeneral,"Exception in Python class: "_..%classname_" - "_exType_" - "_exValue)
        }
    }
    return tSC
}

Method OnInit() As %Status
{
    set tSC = $$$OK

    try {

        if ..%Venv {
            $$$ThrowOnError(##class(IOP.Utils).SetPythonSettings(..%PythonRuntimeLibrary, ..%PythonPath, ..%PythonRuntimeLibraryVersion))
        }

        do ..DisplayPythonVersion()

        do $system.Python.Debugging(..%traceback)

        $$$ThrowOnError(..Connect())

        do ..%class."_debugpy"($this)

        do ..%class."_dispatch_on_init"($this)
    } catch ex {

        set tSC = ..DisplayTraceback(ex)
    }

    quit tSC
}

Method DisplayPythonVersion()
{
    set sys = ##class(%SYS.Python).Import("sys")
    set version = sys.version
    set versionInfo = sys."version_info"
    set major = versionInfo.major
    set minor = versionInfo.minor
    set micro = versionInfo.micro
    set releaseLevel = versionInfo.releaselevel
    set serial = versionInfo.serial

    $$$LOGINFO("Python Version: "_ version)
    $$$LOGINFO("Version Info: "_ major_ "."_ minor_ "."_ micro_" ("_ releaseLevel_ ", "_serial_ ")")
}

ClassMethod SetPythonPath(pClasspaths)
{
    set sys = ##class(%SYS.Python).Import("sys")

    // Add the classpaths to the Python sys.path only if they are not already present
    // Check if the path is already in sys.path
    set found = 0
    for j=1:1:sys.path."__len__"() {
        if sys.path."__getitem__"(j-1) = pClasspaths {
            set found = 1
            quit
        }
    }
    if found = 0 {
        // If not found, add to sys.path
        do sys.path."append"(pClasspaths)
    }
}

Method Connect() As %Status
{
    set tSC = $$$OK
    try {
        // Initialize Python class instance
        $$$ThrowOnError(..InitializePythonClass())
        
        // Set IRIS handles based on component type
        do ..SetIrisHandles()
        
        // Apply property values to Python instance
        do ..SetPropertyValues()
        
        // Notify Python class of connection
        try {
            do ..%class."_dispatch_on_connected"($this)
        } catch ex {
            $$$LOGWARNING(ex.DisplayString())
        }
        
    } catch ex {
        set msg = $System.Status.GetOneStatusText(ex.AsStatus(),1)
        set tSC = $$$ERROR($$$EnsErrGeneral,msg)
    }
    quit tSC
}

Method OnTearDown() As %Status
{
    set tSC = $$$OK
    if $isObject(..%class) {
        try {
            do ..%class."_dispatch_on_tear_down"()
        } catch ex {
            set tSC = ex.AsStatus()
        }
    }
    quit tSC
}

Method SetPropertyValues()
{
    // First process the %settings property
    set remoteSettings = $tr(..%settings,$c(13))
    for i=1:1:$l(remoteSettings,$c(10)) {
        set oneLine = $p(remoteSettings,$c(10),i)
        set property = $p(oneLine,"=",1) continue:property=""
        set value = $p(oneLine,"=",2,*)
        try {
            set $property(..%class,property) = value
        } catch ex {
            $$$LOGWARNING(ex.DisplayString())
        }
    }
    
    // Now process the Python Attributes Settings
    // First list all the properties of the current class
    set class = $CLASSNAME()
    set tSQL = "SELECT * FROM %Dictionary.PropertyDefinition WHERE parent = ?"
    set tSQL = tSQL _ " AND name <> '%timeout'"
    set tSQL = tSQL _ " and name <> '%enable'"
    set tSQL = tSQL _ " and name <> '%classpaths'"
    set tSQL = tSQL _ " and name <> '%classname'"
    set tSQL = tSQL _ " and name <> '%module'"
    set tSQL = tSQL _ " and name <> '%port'"
    set tSQL = tSQL _ " and name <> '%PythonInterpreterPath'"
    set tSQL = tSQL _ " and name <> '%traceback'"
    set tSQL = tSQL _ " and name <> '%PythonPath'"
    set tSQL = tSQL _ " and name <> '%PythonRuntimeLibrary'"
    set tSQL = tSQL _ " and name <> '%PythonRuntimeLibraryVersion'"
    set tSQL = tSQL _ " and name <> '%settings'"
    set tSQL = tSQL _ " and name <> '%Venv'"

    set tStmt = ##class(%SQL.Statement).%New()

    set tSC = tStmt.%Prepare(tSQL)
    if $$$ISERR(tSC) {
        $$$LOGERROR("Error preparing SQL statement: "_tSC)
        quit
    }
    set tRs = tStmt.%Execute(class)

    while tRs.%Next() {
        set property = tRs.%Get("Name")
        set value = $property($this,property)

        if value'="" {
            try {
                set $property(..%class,property) = value
            } catch ex {
                $$$LOGWARNING(ex.DisplayString())
            }
        }
    }

    quit
}

Method dispatchSendRequestSync(
	pTarget,
	pRequest,
	timeout,
	pDescription) As %String
{
    set tSC = ..SendRequestSync(pTarget,pRequest,.objResponse,timeout,pDescription)
    if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
    quit $g(objResponse)
}

Method dispatchSendRequestSyncMultiple(
	pCallStructList As %List,
	pTimeout As %Numeric = -1) As %List
{
    set builtins = ##class(%SYS.Python).Import("builtins")
    // Convert %List to multidimensional array
    set tCallStructList=builtins.len(pCallStructList)
    for i=0:1:builtins.len(pCallStructList)-1 {
        set tCallStructList(i+1) = pCallStructList."__getitem__"(i)
    }

    set tSC = ..SendRequestSyncMultiple(.tCallStructList,pTimeout)
    if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)

    // Convert multidimensional array to Python list
    set tResponseList = builtins.list()
    
    for i=1:1:tCallStructList {
        do tResponseList.append(tCallStructList(i))
    }
    quit tResponseList
}

Method dispatchSendRequestAsync(
	pTarget,
	pRequest,
	pDescription)
{
    set tSC = ..SendRequestAsync(pTarget,pRequest,pDescription)
    if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
    quit
}

ClassMethod OnGetConnections(
	Output pArray As %String,
	pItem As Ens.Config.Item)
{
    // finds any settings of type Ens.DataType.ConfigName
    Try {
        do ..GetPropertyConnections(.pArray,pItem)
    }
    Catch ex {
    }

    // Get settings
    do pItem.GetModifiedSetting("%classpaths", .tClasspaths)
    do pItem.GetModifiedSetting("%classname", .tClassname)
    do pItem.GetModifiedSetting("%module", .tModule)

    // try to instantiate class
    if tClasspaths '="" {
            set sys = ##class(%SYS.Python).Import("sys")
            set delimiter = $s($system.Version.GetOS()="Windows":";",1:":")
            set extraClasspaths = $tr(tClasspaths,delimiter,"|")
            for i=1:1:$l(extraClasspaths,"|") {
                set onePath = $p(extraClasspaths,"|",i)
                set onePath = ##class(%File).NormalizeDirectory(onePath)
                if onePath?1"$$IRISHOME"1P.E set onePath = $e($system.Util.InstallDirectory(),1,*-1)_$e(onePath,11,*)
                if onePath'="" do sys.path.append(onePath)
            }
    }

    set builtins = ##class(%SYS.Python).Import("builtins")
    set module = ##class(%SYS.Python).Import(tModule)
    set class = builtins.getattr(module, tClassname)
    set tClass = class."__new__"(class)

    set tPythonList = tClass."on_get_connections"()
    set tPythonListLen = tPythonList."__len__"()
    for i=0:1:(tPythonListLen-1) {
        set tPythonItem = tPythonList."__getitem__"(i)
        set pArray(tPythonItem) = ""
		#; set ^AALog(pItem.Name,tPythonItem) = ""
    }

    quit
}

Method dispatchSendRequestAsyncNG(
	pTarget,
	pRequest,
	pTimeout,
	pDescription,
	ByRef pMessageHeaderId,
	ByRef pQueueName,
	ByRef pEndTime) As %String
{
	set tSC=$$$OK, tResponse=$$$NULLOREF
	try {

        set tTargetDispatchName=pTarget
        set tTargetConfigName=$get($$$DispatchNameToConfigName(pTarget))
        if tTargetConfigName="" set tSC=$$$EnsError($$$EnsErrBusinessDispatchNameNotRegistered,tTargetDispatchName) quit
        set tTargetBusinessClass = $$$ConfigClassName(tTargetConfigName)
        set tINVOCATION=$classmethod(tTargetBusinessClass,"%GetParameter","INVOCATION")
        if (tINVOCATION'="Queue")&&(tINVOCATION'="InProc") set tSC=$$$ERROR($$$EnsErrParameterInvocationInvalid,tTargetBusinessClass) quit

        quit:$$$ISERR(tSC)
        ;
        set tStartTime=$zh
        set:pTimeout'=-1 tEndTime=$zh+pTimeout

        if tINVOCATION="InProc" {
            set tTimeout=$s(pTimeout=-1:-1,1:tEndTime-$zh)
            if (pTimeout'=-1)&&(tTimeout<0) quit
            set tSC=..SendRequestSync(tTargetConfigName,pRequest,.tResponse,tTimeout,pDescription)
            return tResponse
        } elseif tINVOCATION="Queue" {
            Set tSessionId=..%SessionId
            Set tSuperSession = ..%SuperSession
            Set tSC = ##class(Ens.MessageHeader).NewRequestMessage(.tRequestHeader,pRequest,.tSessionId,.tSuperSession) quit:$$$ISERR(tSC)
            Set ..%SessionId=tSessionId
            Set ..%SuperSession=tSuperSession
            Set tRequestHeader.SourceConfigName = ..%ConfigName
            Set tRequestHeader.TargetConfigName = tTargetConfigName
            Set tRequestHeader.SourceBusinessType = $$$ConfigBusinessType($$$DispatchNameToConfigName(..%ConfigName))
            Set tRequestHeader.TargetBusinessType = $$$ConfigBusinessType($$$DispatchNameToConfigName(tTargetConfigName))
            Set tRequestHeader.TargetQueueName = $$$getConfigQueueName($$$DispatchNameToConfigName(tTargetConfigName),..%SessionId)
            Set tRequestHeader.ReturnQueueName = $$$queueSyncCallQueueName
            Set tRequestHeader.BusinessProcessId = ""
            Set tRequestHeader.Priority = $$$eMessagePriorityAsync
            Set tRequestHeader.Description = pDescription
            Set tSC = ##class(Ens.Queue).Create($$$queueSyncCallQueueName) quit:$$$ISERR(tSC)
            Set tSC = ##class(Ens.Queue).EnQueue(tRequestHeader) quit:$$$ISERR(tSC)
            Set pMessageHeaderId = tRequestHeader.MessageId()
            Set pQueueName = $$$queueSyncCallQueueName
            Set:(pTimeout'=-1) pEndTime = tEndTime
        }
	}
	catch {
		set tSC = $$$EnsSystemError
	}
	quit tSC
}

Method dispatchIsRequestDone(
	pTimeout,
	pEndTime,
	pQueueName,
	pMessageHeaderId,
	ByRef pResponse) As %Status
{

    set tSC=$$$OK
    try {
        set tTimeout=$s(pTimeout=-1:-1,1:pEndTime-$zh)

        set tSC = ##class(Ens.Queue).DeQueue($$$queueSyncCallQueueName,.tResponseHeader,tTimeout,.tIsTimedOut,0) Quit:$$$ISERR(tSC)

        quit:$IsObject(tResponseHeader)=0

        set tFound = $select(tResponseHeader.CorrespondingMessageId: pMessageHeaderId=tResponseHeader.CorrespondingMessageId, 1: 0)
        if tFound=0 {

            set tSC = ##class(Ens.Queue).EnQueue(tResponseHeader)
            Kill $$$EnsActiveMessage($$$SystemName_":"_$Job)
        }
        else {

            if tIsTimedOut || ((pTimeout'=-1)&&(tTimeout<0)) {

                do tResponseHeader.SetStatus($$$eMessageStatusDiscarded)
                return $$$ERROR($$$EnsErrFailureTimeout, tTimeout, $$$StatusDisplayString(tSC), $$$CurrentClass)
            }
            if tResponseHeader.IsError {

                do tResponseHeader.SetStatus($$$eMessageStatusCompleted)
                return $$$EnsError($$$EnsErrGeneral,"Error message received: "_tResponseHeader.ErrorText)
                
            }
            if tResponseHeader.MessageBodyClassName'="" {

                set tResponse = $classmethod(tResponseHeader.MessageBodyClassName,"%OpenId",tResponseHeader.MessageBodyId,,.tSC)
                if '$IsObject(tResponse) return $$$EnsError($$$EnsErrGeneral,"Could not open MessageBody "_tResponseHeader.MessageBodyId_" for MessageHeader #"_tResponseHeader.%Id()_" with body class "_tResponseHeader.MessageBodyClassName_":"_$$$StatusDisplayString(tSC)) 
            } else {

                set tResponse=$$$NULLOREF
            }
            set pResponse=tResponse
            do tResponseHeader.SetStatus($$$eMessageStatusCompleted)
            set tSC = 2

        }
    }
	catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

XData MessageMap
{
<MapItems>
<MapItem MessageType="IOP.Generator.Message.Start"><Method>OnMsgGeneratorStart</Method></MapItem>
<MapItem MessageType="IOP.Generator.Message.Stop"><Method>OnMsgGeneratorStop</Method></MapItem>
<MapItem MessageType="IOP.Generator.Message.Poll"><Method>OnMsgGeneratorPoll</Method></MapItem>
</MapItems>
}

Method OnMsgGeneratorStart(
	pRequest As IOP.Generator.Message.Start,
	Output pResponse As %Library.Persistent) As %Status
{
    #dim tSC As %Status = $$$OK
	try {
		set pResponse = ..%class."_dispatch_generator_started"(pRequest)
	} catch ex {
		set tSC = ..DisplayTraceback(ex)
	}
	quit tSC
}

Method OnMsgGeneratorStop(
	pRequest As IOP.Generator.Message.Stop,
	Output pResponse As %Library.Persistent) As %Status
{
    #dim tSC As %Status = $$$OK

	try {
		set pResponse = ..%class."_dispatch_generator_stopped"(pRequest)
	} catch ex {
		set tSC = ..DisplayTraceback(ex)
	}
	quit tSC
}

Method OnMsgGeneratorPoll(
	pPollIn As IOP.Generator.Message.Poll,
	Output pResponse As %Library.Persistent) As %Status
{
    #dim tSC As %Status = $$$OK
    set tSC = $$$OK
    try {
        set pResponse = ..%class."_dispatch_generator_poll"()
    } catch ex {
        set tSC = ..DisplayTraceback(ex)
    }
    quit tSC
}

Method InitializePythonClass() As %Status [ Private ]
{
    set tSC = $$$OK
    try {
        // Check if module is already imported
        set sys = ##class(%SYS.Python).Import("sys")
        set module = sys.modules.get(..%module, $$$NULLOREF)
        
        if $isObject(module) {
            $$$LOGINFO("Module "_..%module_" is already imported in sys.modules")
            set ..%class = ..CreateClassInstance(module)
        } else {
            // Setup classpaths if specified
            if ..%classpaths '= "" {
                do ..SetupClasspaths()
            }
            
            // Import module and create class instance
            set module = ##class(%SYS.Python).Import(..%module)
            set ..%class = ..CreateClassInstance(module)
        }
    } catch ex {
        set tSC = ex.AsStatus()
    }
    quit tSC
}

Method CreateClassInstance(module As %SYS.Python) As %SYS.Python [ Private ]
{
    set builtins = ##class(%SYS.Python).Import("builtins")
    set class = builtins.getattr(module, ..%classname)
    quit class."__new__"(class)
}

Method SetupClasspaths() [ Private ]
{
    set delimiter = $s($system.Version.GetOS()="Windows":";",1:":")
    set extraClasspaths = $tr(..%classpaths, delimiter, "|")
    
    for i=1:1:$l(extraClasspaths,"|") {
        set onePath = $p(extraClasspaths,"|",i)
        set onePath = ##class(%File).NormalizeDirectory(onePath)
        do ..SetPythonPath(onePath)
    }
}

Method SetIrisHandles() [ Private ]
{
    if ..%Extends("IOP.InboundAdapter") || ..%Extends("IOP.OutboundAdapter") {
        do ..%class."_set_iris_handles"($this, ..BusinessHost)
    } elseif $this.%Extends("IOP.BusinessProcess") {
        do ..%class."_set_iris_handles"($this, $$$NULLOREF)
    } else {
        do ..%class."_set_iris_handles"($this, ..Adapter)
    }
}

}
