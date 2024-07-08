/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Include Ensemble

Class IOP.Common [ Abstract, ClassType = "", ProcedureBlock, System = 4 ]
{

/// One or more Classpaths (separated by '|' character) needed in addition to the ones configured in the Java Gateway Service
Property %classpaths As %String(MAXLEN = "");

Property %classname As %String(MAXLEN = "");

Property %module As %String(MAXLEN = "");

Property %settings As %String(MAXLEN = "");

/// Instance of class
Property %class As %SYS.Python;

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

Method OnInit() As %Status
{
    set tSC = $$$OK
    try {
        $$$ThrowOnError(..Connect())
        do ..%class."_dispatch_on_init"($this)
    } catch ex {
        set tSC = ex.AsStatus()
    }
    quit tSC
}

ClassMethod SetPythonPath(pClasspaths)
{
    set sys = ##class(%SYS.Python).Import("sys")

    for i=0:1:(sys.path."__len__"()-1) {
        Try {
            if sys.path."__getitem__"(i) = pClasspaths {
                do sys.path."__delitem__"(i)
            }
        }
        Catch ex {
            // do nothing
        }

    }
    do sys.path.insert(0, pClasspaths)
}

Method Connect() As %Status
{
    set tSC = $$$OK
    try {
        
        set container = $this
        
        //set classpass
        if ..%classpaths '="" {
            set delimiter = $s($system.Version.GetOS()="Windows":";",1:":")
            set extraClasspaths = $tr(container.%classpaths,delimiter,"|")
            for i=1:1:$l(extraClasspaths,"|") {
                set onePath = $p(extraClasspaths,"|",i)
                set onePath = ##class(%File).NormalizeDirectory(onePath)
                do ..SetPythonPath(onePath)
            }
        }
        if $isObject(..%class)=0 {
            set importlib = ##class(%SYS.Python).Import("importlib")
            set builtins = ##class(%SYS.Python).Import("builtins")
            set module = importlib."import_module"(..%module)
            set class = builtins.getattr(module, ..%classname)
            set ..%class = class."__new__"(class)
        }
        ;
        if ..%Extends("IOP.InboundAdapter") || ..%Extends("IOP.OutboundAdapter") {
            do ..%class."_set_iris_handles"($this,..BusinessHost)
        } elseif $this.%Extends("IOP.BusinessProcess") {
            do ..%class."_set_iris_handles"($this,$$$NULLOREF)
        } else {
            do ..%class."_set_iris_handles"($this,..Adapter)
        }
        ;
        do ..SetPropertyValues()
        ;
        try {
            do ..%class."_dispatch_on_connected"($this)
        } catch ex {
            $$$LOGWARNING(ex.DisplayString())
        }
        ;
    } catch ex {
        set msg = $System.Status.GetOneStatusText(ex.AsStatus(),1)
        set tSC = $$$ERROR($$$EnsErrGeneral,msg)
    }
    quit tSC
}

Method OnTearDown() As %Status
{
    set tSC = $$$OK
    do ..%class."_dispatch_on_tear_down"()
    quit tSC
}

Method SetPropertyValues()
{
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
    quit
}

Method dispatchSendRequestSync(
	target,
	request,
	timeout,
	description) As %String
{
    set tSC = ..SendRequestSync(target,request,.objResponse,timeout,description)
    if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
    quit $g(objResponse)
}

Method dispatchSendRequestAsync(
	target,
	request,
	description)
{
    set tSC = ..SendRequestAsync(target,request,description)
    if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
    quit
}

ClassMethod OnGetConnections(
	Output pArray As %String,
	pItem As Ens.Config.Item)
{
    // finds any settings of type Ens.DataType.ConfigName
    do ..GetPropertyConnections(.pArray,pItem)

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
    set importlib = ##class(%SYS.Python).Import("importlib")
    set builtins = ##class(%SYS.Python).Import("builtins")
    set module = importlib."import_module"(tModule)
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

}
