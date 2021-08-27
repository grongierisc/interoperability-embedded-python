/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Include Ensemble

Class EnsLib.PEX.Common [ Abstract, ClassType = "", ProcedureBlock, System = 4 ]
{

/// External Language Server Name. Once specified, it supersedes the settings in Gateway Host and Gateway Port.
/// Using External Language Server is preferred over Gateway Host and Gateway Port.
Property %gatewayName As %String [ Internal ];

/// Gateway Host. Using External Language Server is preferred.
Property %gatewayHost As %String [ Internal ];

/// Gateway Port. Using External Language Server is preferred.
Property %gatewayPort As %Integer [ Internal ];

/// Number of seconds to wait on each attempt to connect to the Gateway
Property %gatewayTimeout As %Numeric(MAXVAL = 30000, MINVAL = 0) [ InitialExpression = 5 ];

/// One or more Classpaths (separated by '|' character) needed in addition to the ones configured in the Java Gateway Service
Property %gatewayExtraClasspaths As %String(MAXLEN = "");

/// The Gateway connection object
Property %gatewayConnection As %Net.Remote.Gateway;

/// The proxy object for the Gateway connection
Property %gatewayProxy As %RegisteredObject;

Property %remoteClassname As %String(MAXLEN = "") [ Internal ];

Property %remoteSettings As %String(MAXLEN = "") [ Internal ];

Method OnInit() As %Status
{
	set tSC = $$$OK
	try {
		set tSC = ..CheckGatewayConnection() quit:$$$ISERR(tSC)
		do ..%gatewayProxy."_dispatchOnInit"($this)
	} catch ex {
		set tSC = ex.AsStatus()
		do ..CheckGatewayDisconnection()
	}
	quit tSC
}

Method OnTearDown() As %Status
{
	set tSC = $$$OK
	try {
		set tSC = ..CheckGatewayConnection() quit:$$$ISERR(tSC)
		do ..%gatewayProxy."_dispatchOnTearDown"($this)
	} catch ex {
		set tSC = ex.AsStatus()
	}
	do ..Disconnect()
	quit tSC
}

Method Connect() As %Status
{
	set tSC = $$$OK
	try {
		if ..%Extends("EnsLib.PEX.InboundAdapter") || ..%Extends("EnsLib.PEX.OutboundAdapter") {
			set container = $s(..%useHostConnection:..BusinessHost,1:$this)
		} else {
			set container = $this
		}
		;
		if $isObject(container.%gatewayConnection)=0||container.%gatewayConnection.Closed {
			if container.%gatewayName'="" {
				set container.%gatewayConnection = $system.external.getGateway(container.%gatewayName)
			} else {
				set container.%gatewayConnection = $system.external.getRemoteGateway(container.%gatewayHost,container.%gatewayPort,container.%gatewayTimeout)
			}
			;
			set classpaths = ##class(%ListOfDataTypes).%New()
			set delimiter = $s($system.Version.GetOS()="Windows":";",1:":")
			set extraClasspaths = $tr(container.%gatewayExtraClasspaths,delimiter,"|")
			for i=1:1:$l(extraClasspaths,"|") {
				set onePath = $p(extraClasspaths,"|",i)
				if onePath?1"$$IRISHOME"1P.E set onePath = $e($system.Util.InstallDirectory(),1,*-1)_$e(onePath,11,*)
				if onePath'="" do classpaths.Insert(onePath)
			}
			do container.%gatewayConnection.addToPath(classpaths)
		}
		if container'=$this set ..%gatewayConnection = container.%gatewayConnection
		;
		if $isObject(..%gatewayProxy)=0 {
			set ..%gatewayProxy = ..%gatewayConnection.new(..%remoteClassname)
		}
		;
		if ..%Extends("EnsLib.PEX.InboundAdapter") || ..%Extends("EnsLib.PEX.OutboundAdapter") {
			do ..%gatewayProxy."_setIrisHandles"($this,..BusinessHost)
		} elseif $this.%Extends("EnsLib.PEX.BusinessProcess") {
			do ..%gatewayProxy."_setIrisHandles"($this,$$$NULLOREF)
		} else {
			do ..%gatewayProxy."_setIrisHandles"($this,..Adapter)
		}
		;
		do ..SetPropertyValues()
		;
		try {
			do ..%gatewayProxy."_dispatchOnConnected"($this)
		} catch ex {
			$$$LOGWARNING(ex.DisplayString())
		}
		;
	} catch ex {
		set tSC = ex.AsStatus()
	}
	if $$$ISERR(tSC) set (..%gatewayConnection,..%gatewayProxy) = $$$NULLOREF
	quit tSC
}

Method Disconnect() As %Status
{
	if ..%Extends("EnsLib.PEX.InboundAdapter") || ..%Extends("EnsLib.PEX.OutboundAdapter") {
		set container = $s(..%useHostConnection:..BusinessHost,1:$this)
	} else {
		set container = $this
	}
	if $isObject(container.%gatewayConnection) do ..%gatewayConnection.%Disconnect()
	set (container.%gatewayConnection,container.%gatewayProxy) = $$$NULLOREF
	set (..%gatewayConnection,..%gatewayProxy) = $$$NULLOREF
	quit $$$OK
}

Method CheckGatewayDisconnection() As %Boolean
{
	set isConnected = 0
	if ..%Extends("EnsLib.PEX.InboundAdapter") || ..%Extends("EnsLib.PEX.OutboundAdapter") {
		set container = $s(..%useHostConnection:..BusinessHost,1:$this)
	} else {
		set container = $this
	}
	try { set isConnected = $$$ISOK(container.%gatewayConnection.%Ping(,,,1,container.%gatewayConnection.GatewayDevice)) } catch {}
	if 'isConnected {
		set (container.%gatewayConnection,container.%gatewayProxy) = $$$NULLOREF
		set (..%gatewayConnection,..%gatewayProxy) = $$$NULLOREF
	}
	quit isConnected
}

Method CheckGatewayConnection() As %Status
{
	quit ..Connect()
}

Method SetPropertyValues()
{
	set remoteSettings = $tr(..%remoteSettings,$c(13))
	for i=1:1:$l(remoteSettings,$c(10)) {
		set oneLine = $p(remoteSettings,$c(10),i)
		set property = $p(oneLine,"=",1) continue:property=""
		set value = $p(oneLine,"=",2,*)
		try {
			set $property(..%gatewayProxy,property) = value
		} catch ex {
			$$$LOGWARNING(ex.DisplayString())
		}
	}
	quit
}

Method dispatchSendRequestSync(target, request, timeout, description) As %String
{
	if request'="",$isObject(request)=0 set request = ..deserialize(request)
	set tSC = ..SendRequestSync(target,request,.objResponse,timeout,description)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	if $isObject($g(objResponse)),objResponse.%IsA("EnsLib.PEX.Message") set objResponse = ..serialize(objResponse)
	quit $g(objResponse)
}

Method dispatchSendRequestAsync(target, request, description)
{
	if request'="",$isObject(request)=0 set request = ..deserialize(request)
	set tSC = ..SendRequestAsync(target,request,description)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit
}

ClassMethod serialize(message As EnsLib.PEX.Message) As %String
{
	if $g(message)=$$$NULLOREF quit ""
	quit message.%classname_":"_message.%jsonObject.%ToJSON()
}

ClassMethod deserialize(serialized As %String = "") As EnsLib.PEX.Message
{
	if serialized = "" {
		set message = $$$NULLOREF
	} else {
		set message = ##class(EnsLib.PEX.Message).%New()
		set message.%classname = $p(serialized,":",1)
		set json = $p(serialized,":",2,*)
		if json="" set json = "{}"
		set message.%jsonObject = ##class(%DynamicObject).%FromJSON(json)
	}
	quit message
}

ClassMethod OnGetConnections(Output pArray As %String, pItem As Ens.Config.Item)
{
	try {
		// finds any settings of type Ens.DataType.ConfigName
		do ..GetPropertyConnections(.pArray,pItem)
		// establishes connection to remote class and calls it's OnGetConnections
		do pItem.GetSetting("%gatewayName", .gatewayName)
		if gatewayName'="" {
			set connection = $system.external.getGateway(gatewayName)
		} else {
			do pItem.GetSetting("%gatewayHost", .host)
			do pItem.GetSetting("%gatewayPort", .port)
			do pItem.GetSetting("%gatewayTimeout", .timeout)
			set connection = $system.external.getRemoteGateway(host,port,timeout)
		}
		if $isobject(connection)=0 {
			quit	
		}
		set classpaths = ##class(%ListOfDataTypes).%New()
		set delimiter = $s($system.Version.GetOS()="Windows":";",1:":")
		do pItem.GetSetting("%gatewayExtraClasspaths", .gatewayExtraClasspaths)
		set extraClasspaths = $tr(gatewayExtraClasspaths,delimiter,"|")
		for i=1:1:$l(extraClasspaths,"|") {
			set onePath = $p(extraClasspaths,"|",i)
			if onePath?1"$$IRISHOME"1P.E set onePath = $e($system.Util.InstallDirectory(),1,*-1)_$e(onePath,11,*)
			if onePath'="" do classpaths.Insert(onePath)
		}
		do connection.addToPath(classpaths)
		;
		do pItem.GetSetting("%remoteClassname", .remoteClassname)
		set targets = connection.invoke(remoteClassname, "OnGetConnections")
		for i=1:1:$listlength(targets) {
			set pArray($list(targets, i))=""
		}
	} catch ex {
	}
}

}
