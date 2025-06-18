/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.DuplexProcess Extends IOP.BusinessProcess [ ClassType = persistent, ProcedureBlock, System = 4 ]
{

/// Domain for Text localization
Parameter DOMAIN = "PrivateSession";

/// The Duplex Service name. This property is set at runtime after receiving the primary request
Property ServiceDuplexName As %String;

/// Indicates if a given ConfigItem is in private session or not
Property %IsInPrivateSession As array Of %Boolean(STORAGEDEFAULT = "list");

/// This method is always called asynchronously ONCE at the beginning of the process
Method OnRequest(
	pRequest As %Library.Persistent,
	Output pResponse As Ens.Response) As %Status
{
	#dim tSC As %Status = $$$OK
	try {
		If $IsObject(pRequest)&&($classname(pRequest)="IOP.PrivateSession.Message.Start") {
			Set tSC=..Reply(##class(IOP.PrivateSession.Message.Ack).%New()) Quit:$$$ISERR(tSC)
			Set ..ServiceDuplexName = ..%PrimaryRequestHeader.SourceConfigName
			Do ..IsInPrivateSessionSet(..ServiceDuplexName,1)
			Set tSC=..SendRequestAsync(..ServiceDuplexName,##class(IOP.PrivateSession.Message.Poll).%New(),1) Quit:$$$ISERR(tSC)
			Set tSC=..OnPrivateSessionStarted(..ServiceDuplexName,0) Quit:$$$ISERR(tSC)
		} Else {
			Set tSC=..OnDocument(..%PrimaryRequestHeader.SourceConfigName,pRequest)
		}
	} catch {
		Set tSC=$$$EnsSystemError
	}
	Quit tSC
}

/// Handle a 'Response'
Method OnResponse(
	request As %Library.Persistent,
	ByRef response As %Library.Persistent,
	callrequest As %Library.Persistent,
	callresponse As %Library.Persistent,
	pCompletionKey As %String) As %Status
{
	#dim tSC As %Status = $$$OK
	#dim tSourceConfigName, tOneConfigName As %String
	try {
		; get the SourceConfigName of this message
		Set tSourceConfigName=..%CurrentResponseHeader.SourceConfigName
		; handle SessionStop message
		If $IsObject(callresponse)&&($classname(callresponse)="IOP.PrivateSession.Message.Ack") {
			Do ..IsInPrivateSessionSet(tSourceConfigName,1)
			Set tSC=..SendRequestAsync(tSourceConfigName,##class(IOP.PrivateSession.Message.Poll).%New(),1) Quit:$$$ISERR(tSC)
			Set tSC=..OnPrivateSessionStarted(tSourceConfigName,1) Quit:$$$ISERR(tSC)
			Quit
		}
		; handle SessionStop message
		If $IsObject(callresponse)&&($classname(callresponse)="IOP.PrivateSession.Message.Stop") {
			Set tSC=..UnRegisterPrivateSession(tSourceConfigName) Quit:$$$ISERR(tSC)
			Set tSC=..OnPrivateSessionStopped(tSourceConfigName,0,callresponse.AttachedMessage) Quit:$$$ISERR(tSC)
			Quit
		}
		; send poll request again back to the same ConfigItem if this this is in response to a poll request
		If $IsObject(callrequest)&&($classname(callrequest)="IOP.PrivateSession.Message.Poll") {
			If ..IsInPrivateSession(tSourceConfigName) {
				Set tSC=..SendRequestAsync(tSourceConfigName,##class(IOP.PrivateSession.Message.Poll).%New(),1) If $$$ISERR(tSC)
			}
		}
		; call OnDocument
		Set tSC=..OnDocument(tSourceConfigName,callresponse) Quit:$$$ISERR(tSC)
	} catch {
		Set tSC=$$$EnsSystemError
	}
	Quit tSC
}

Method StartPrivateSession(pDuplexConfigName As %String = "") As %Status
{
	#dim tSC As %Status = $$$OK
	try {
		If pDuplexConfigName="" Set tSC=$$$EnsError($$$EnsErrGeneral,"Duplex configuration name is missing") Quit
		If ..IsInPrivateSession(pDuplexConfigName) Quit
		Set tSC=..SendRequestAsync(pDuplexConfigName,##class(IOP.PrivateSession.Message.Start).%New()) Quit:$$$ISERR(tSC)
	} catch {
		Set tSC=$$$EnsSystemError
	}
	Quit tSC
}

Method StopPrivateSession(
	pDuplexConfigName As %String = "",
	pAttachedMessage As %Persistent = "") As %Status
{
	#dim tSC As %Status = $$$OK
	try {
		If pDuplexConfigName="" Set tSC=$$$EnsError($$$EnsErrGeneral,"Duplex configuration name is missing") Quit
		If '..IsInPrivateSession(pDuplexConfigName) Quit
		Set tSC=..SendRequestAsync(pDuplexConfigName,##class(IOP.PrivateSession.Message.Stop).%New(pAttachedMessage),0) Quit:$$$ISERR(tSC)
		Set tSC=..UnRegisterPrivateSession(pDuplexConfigName)
		Set tSC=..OnPrivateSessionStopped(pDuplexConfigName,1) Quit:$$$ISERR(tSC)
	} catch {
		Set tSC=$$$EnsSystemError
	}
	Quit tSC
}

Method StopAllPrivateSessions(pAttachedMessage As %Persistent = "") As %Status
{
	#dim tSC As %Status = $$$OK
	#dim tItem As %String
	try {
		Set tItem="" For  {
			Set tItem=..%IsInPrivateSession.Next(tItem) Quit:tItem=""
			Set tSC=..StopPrivateSession(tItem,pAttachedMessage) Quit:$$$ISERR(tSC)
		}
	} catch {
		Set tSC=$$$EnsSystemError
	}
	Quit tSC
}

Method UnRegisterPrivateSession(pDuplexConfigName As %String) As %String
{
	#dim tSC As %Status = $$$OK
	try {
		For i=..%MasterPendingResponses.Count():-1:1 {
			Set tRequestHeader=##class(Ens.MessageHeader).%OpenId($li(..%MasterPendingResponses.GetAt(i),1))
			If $IsObject(tRequestHeader),tRequestHeader.TargetConfigName=pDuplexConfigName,tRequestHeader.MessageBodyClassName="IOP.PrivateSession.Message.Poll" {
				Do ..%MasterPendingResponses.RemoveAt(i)
			}
		}
		Do ..IsInPrivateSessionSet(pDuplexConfigName,0)
	} catch {
		Set tSC=$$$EnsSystemError
	}
	Quit tSC
}

Method IsInPrivateSessionSet(
	pDuplexConfigName As %String,
	pInPrivateSession As %Boolean)
{
	If pInPrivateSession {
		Do ..%IsInPrivateSession.SetAt(1,pDuplexConfigName)
	} Else {
		Do ..%IsInPrivateSession.RemoveAt(pDuplexConfigName)
	}
	Quit
}

Method IsInPrivateSession(pDuplexConfigName As %String) As %Boolean
{
	If pDuplexConfigName="" Quit 0
	Quit ..%IsInPrivateSession.IsDefined(pDuplexConfigName)
}

Method OnDocument(
	pSourceConfigName As %String,
	pInput As %Library.Persistent) As %Status
{
	set tSC = $$$OK
	try {
		set response = ..%class."_dispatch_on_document"($this,pSourceConfigName,pInput)
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

Method OnPrivateSessionStarted(
	pSourceConfigName As %String,
	pSelfGenerated As %Boolean) As %Status
{
	set tSC = $$$OK
	try {
		set response = ..%class."_dispatch_on_private_session_started"($this,pSourceConfigName,pSelfGenerated)
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

Method OnPrivateSessionStopped(
	pSourceConfigName As %String,
	pSelfGenerated As %Boolean,
	pAttachedMessage As %Persistent = "") As %Status
{
	set tSC = $$$OK
	try {
		set response = ..%class."_dispatch_on_private_session_stopped"($this,pSourceConfigName,pSelfGenerated,pAttachedMessage)
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

Storage Default
{
<Data name="ProcessDefaultData">
<Subscript>"Process"</Subscript>
<Value name="1">
<Value>ServiceDuplexName</Value>
</Value>
<Value name="2">
<Value>%IsInPrivateSession</Value>
</Value>
<Value name="3">
<Value>%classpaths</Value>
</Value>
<Value name="4">
<Value>%classname</Value>
</Value>
<Value name="5">
<Value>%module</Value>
</Value>
<Value name="6">
<Value>%settings</Value>
</Value>
<Value name="7">
<Value>%class</Value>
</Value>
</Data>
<DefaultData>ProcessDefaultData</DefaultData>
<Type>%Storage.Persistent</Type>
}

}
