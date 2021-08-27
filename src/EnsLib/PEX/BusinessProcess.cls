/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class EnsLib.PEX.BusinessProcess Extends (Ens.BusinessProcess, EnsLib.PEX.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%remoteClassname:Remote BusinessProcess,%remoteSettings:Remote BusinessProcess,%gatewayName:Remote BusinessProcess,%gatewayHost:Remote BusinessProcess,%gatewayPort:Remote BusinessProcess,%gatewayTimeout:Remote BusinessProcess,%gatewayExtraClasspaths:Remote BusinessProcess";

Property persistentProperties As array Of %String(MAXLEN = "");

Method dispatchSendRequestAsync(target, request, responseRequired, completionkey, description)
{
	if request'="",$isObject(request)=0 set request = ..deserialize(request)
	set tSC = ..SendRequestAsync(target,request,responseRequired,completionkey,description)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit
}

Method dispatchReply(response)
{
	if response'="",$isObject(response)=0 set response = ..deserialize(response)
	set tSC = ..Reply(response)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit
}

Method dispatchSetTimer(timeout, completionKey)
{
	set tSC = ..SetTimer(timeout,$g(completionKey))
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit
}

Method OnRequest(request As %Persistent, Output response As %Persistent) As %Status
{
	set tSC = $$$OK
	try {
		set tSC = ..CheckGatewayConnection() quit:$$$ISERR(tSC)
		if $isObject(request),request.%IsA("EnsLib.PEX.Message") set request = ..serialize(request)
		set response = ..%gatewayProxy."_dispatchOnRequest"($this,request)
		if response'="",$isObject(response)=0 set response = ..deserialize(response)
	} catch ex {
		set tSC = ex.AsStatus()
		do ..CheckGatewayDisconnection()
	}
	quit tSC
}

/// Handle a 'Response'
Method OnResponse(request As %Persistent, ByRef response As %Persistent, callRequest As %Persistent, callResponse As %Persistent, pCompletionKey As %String) As %Status
{
	set tSC = $$$OK
	try {
		set tSC = ..CheckGatewayConnection() quit:$$$ISERR(tSC)
		if $isObject(request),request.%IsA("EnsLib.PEX.Message") set request = ..serialize(request)
		if $isObject(response),response.%IsA("EnsLib.PEX.Message") set response = ..serialize(response)
		if $isObject(callRequest),callRequest.%IsA("EnsLib.PEX.Message") set callRequest = ..serialize(callRequest)
		if $isObject(callResponse),callResponse.%IsA("EnsLib.PEX.Message") set callResponse = ..serialize(callResponse)
		set response = ..%gatewayProxy."_dispatchOnResponse"($this,request,response,callRequest,callResponse,pCompletionKey)
		if response'="",$isObject(response)=0 set response = ..deserialize(response)
	} catch ex {
		set tSC = ex.AsStatus()
		do ..CheckGatewayDisconnection()
	}
	quit tSC
}

Method OnComplete(request As %Library.Persistent, ByRef response As %Library.Persistent) As %Status
{
	set tSC = $$$OK
	try {
		set tSC = ..CheckGatewayConnection() quit:$$$ISERR(tSC)
		if $isObject(request),request.%IsA("EnsLib.PEX.Message") set request = ..serialize(request)
		if $isObject(response),response.%IsA("EnsLib.PEX.Message") set response = ..serialize(response)
		set response = ..%gatewayProxy."_dispatchOnComplete"($this,request,response)
		if response'="",$isObject(response)=0 set response = ..deserialize(response)
	} catch ex {
		set tSC = ex.AsStatus()
		do ..CheckGatewayDisconnection()
	}
	quit tSC
}

Method getPersistentProperty(name)
{
	quit ..persistentProperties.GetAt(name)
}

Method setPersistentProperty(name, value)
{
	quit ..persistentProperties.SetAt(value,name)
}


}
