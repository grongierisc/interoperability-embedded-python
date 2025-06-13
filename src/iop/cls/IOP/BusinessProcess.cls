/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.BusinessProcess Extends (Ens.BusinessProcess, IOP.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%classname:Python BusinessProcess,%module:Python BusinessProcess,%settings:Python BusinessProcess,%classpaths:Python BusinessProcess";

Property persistentProperties As array Of %String(MAXLEN = "");

Method dispatchReply(response)
{
	set tSC = ..Reply(response)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit
}

Method dispatchSetTimer(
	timeout,
	completionKey)
{
	set tSC = ..SetTimer(timeout,$g(completionKey))
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit
}

Method dispatchSendRequestAsync(
	target,
	request,
	responseRequired,
	completionKey,
	description)
{
	Try {
		$$$ThrowOnError(..SendRequestAsync(target,request,responseRequired,completionKey,description))
	}
	Catch ex {
		set tSC = ..DisplayTraceback(ex)
	}

    quit
}

Method OnRequest(
	request As %Persistent,
	Output response As %Persistent) As %Status
{
	set tSC = $$$OK
	try {
		set response = ..%class."_dispatch_on_request"($this,request)
	} catch ex {
		set tSC = ..DisplayTraceback(ex)
	}
	quit tSC
}

/// Handle a 'Response'
Method OnResponse(
	request As %Persistent,
	Output response As %Persistent,
	callRequest As %Persistent,
	callResponse As %Persistent,
	pCompletionKey As %String) As %Status
{
	set tSC = $$$OK
	try {
		set response = ..%class."_dispatch_on_response"($this,request,response,callRequest,callResponse,pCompletionKey)
	} catch ex {
		set tSC = ..DisplayTraceback(ex)
	}
	quit tSC
}

Method OnComplete(
	request As %Library.Persistent,
	ByRef response As %Library.Persistent) As %Status
{
	set tSC = $$$OK
	try {
		set response = ..%class."_dispatch_on_complete"($this,request,response)
	} catch ex {
		set tSC = ..DisplayTraceback(ex)
	}
	quit tSC
}

Method getPersistentProperty(name)
{
	quit ..persistentProperties.GetAt(name)
}

Method setPersistentProperty(
	name,
	value)
{
	quit ..persistentProperties.SetAt(value,name)
}

Storage Default
{
<Data name="BusinessProcessDefaultData1">
<Subscript>"BusinessProcess"</Subscript>
<Value name="1">
<Value>%classpaths</Value>
</Value>
<Value name="2">
<Value>%classname</Value>
</Value>
<Value name="3">
<Value>%module</Value>
</Value>
<Value name="4">
<Value>%settings</Value>
</Value>
<Value name="5">
<Value>%class</Value>
</Value>
<Value name="6">
<Value>%enable</Value>
</Value>
<Value name="7">
<Value>%timeout</Value>
</Value>
<Value name="8">
<Value>%port</Value>
</Value>
<Value name="9">
<Value>%PythonInterpreterPath</Value>
</Value>
<Value name="10">
<Value>%traceback</Value>
</Value>
<Value name="11">
<Value>%PythonPath</Value>
</Value>
<Value name="12">
<Value>%PythonRuntimeLibrary</Value>
</Value>
<Value name="13">
<Value>%PythonRuntimeLibraryVersion</Value>
</Value>
<Value name="14">
<Value>%Venv</Value>
</Value>
</Data>
<Data name="persistentProperties">
<Attribute>persistentProperties</Attribute>
<Structure>subnode</Structure>
<Subscript>"IOP.BusinessProcess.persistentProperties"</Subscript>
</Data>
<DefaultData>BusinessProcessDefaultData1</DefaultData>
<Type>%Storage.Persistent</Type>
}

}
