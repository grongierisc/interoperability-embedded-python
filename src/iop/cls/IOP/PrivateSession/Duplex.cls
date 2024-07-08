/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.PrivateSessionDuplex Extends (IOP.Common, Ens.BusinessDuplex) [ Abstract, System = 4 ]
{

/// Domain for error messages   
Parameter DOMAIN = "PrivateSession";

Parameter SETTINGS = "DuplexTargetConfigName,%classname:Python BusinessProcess,%module:Python BusinessProcess,%settings:Python BusinessProcess,%classpaths:Python BusinessProcess";

/// Configuration item(s) to which to send messages
Property DuplexTargetConfigName As %String(MAXLEN = 1000);

/// This holds the deferred response token
Property DeferredResponseToken As %String;

/// This holds data that is not yet ready for processing
Property ReceivedDataQueue As list Of %Library.Persistent;

/// This method is called by the TCP Adapter when a message is received.
Method OnProcessInput(
	pInput As %Persistent,
	Output pOutput As %Persistent,
	ByRef pHint As %String) As %Status
{
	set tSC = $$$OK
	try {
		try {
			set ..%class."_wait_for_next_call_interval" = ..%WaitForNextCallInterval
		}catch {}
            set pOutput = ..%class."_dispatch_on_process_input"(pInput)
		try {
			set ..%WaitForNextCallInterval = ..%class."_wait_for_next_call_interval"
		}catch {}
} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

Method dispatchSendDocumentToProcess(pDocument) As %String
{
	set tSC = ..SendDocumentToProcess(pDocument)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit
}

Method SendDocumentToProcess(pDocument As %Library.Persistent) As %Status
{
    #dim tSC As %Status = $$$OK
    try {
        If '..%InPrivateSession Set tSC=..StartPrivateSession() Quit:$$$ISERR(tSC)
        If ..DeferredResponseToken'="" {
            Set tSC=..SendDeferredResponse(..DeferredResponseToken,pDocument) If $$$ISERR(tSC) Quit
            Set ..DeferredResponseToken=""
        } else {
            Do ..ReceivedDataQueue.Insert(pDocument)
        }
    } catch {
        Set tSC=$$$EnsSystemError
    }
    Quit tSC
}

Method StartPrivateSession() As %Status
{
    #dim tSC As %Status = $$$OK
    try {
        If ..%InPrivateSession Quit
        Set tSC = ..RegisterPrivateSession() Quit:$$$ISERR(tSC)
        Set tSC=..SendRequestAsync(..DuplexTargetConfigName,##class(IOP.PrivateSession.Message.Start).%New()) Quit:$$$ISERR(tSC)
        Set tSC = ..OnPrivateSessionStarted(1) Quit:$$$ISERR(tSC)
    } catch {
        Set tSC=$$$EnsSystemError
    }
    Quit tSC
}

Method StopPrivateSession(pAttachedMessage As %Persistent = "") As %Status
{
    #dim tSC As %Status = $$$OK
    #dim tMessageHeaderId As %String
    #dim tRequestHeader As Ens.MessageHeader
    try {
	    If ..%InPrivateSession {
	        #; Target might receive stop message before this job unregisters and therefore need to remove queue pointer 
	        If ..DeferredResponseToken'="" {
		        try {
					Set tMessageHeaderId=$p(..DeferredResponseToken,"|",1)
					Set tRequestHeader=##Class(Ens.MessageHeader).%OpenId(tMessageHeaderId,,.tSC) Quit:$$$ISERR(tSC)
					If $$$ConfigSessionQueueName(..%ConfigName,..%PrivateSessionId)'=tRequestHeader.ReturnQueueName {
			        	Kill $$$ConfigSessionQueueName(..%ConfigName,..%PrivateSessionId)
					}
					Set tRequestHeader=""
		        } catch {}
	        }
			Set tSC=..SendDocumentToProcess(##class(IOP.PrivateSession.Message.Stop).%New(pAttachedMessage)) Quit:$$$ISERR(tSC)
            Set tSC=..UnRegisterPrivateSession()
            set ..DeferredResponseToken=""
            
            #; Ensure all messages are delivered including STOP message (JN1098)
            #; Do ..ReceivedDataQueue.Clear()
            Set tSC=..OnPrivateSessionStopped(1) Quit:$$$ISERR(tSC)
        }
    } catch {
        Set tSC=$$$EnsSystemError
    }
    Quit tSC
}

Method RegisterPrivateSession() As %Status
{
	If ..%InPrivateSession Quit $$$OK
	If ..%SessionId="" Set tSC=..ForceSessionId() Quit:$$$ISERR(tSC) tSC
	Set ..%PrivateSessionId=..%SessionId
	Set tSC = ##class(Ens.Queue).Create(..QueueName()) Quit:$$$ISERR(tSC) tSC

    try {
        Set tSC=..Adapter.OpenEventDevice() 
    }
    catch {

    }
	
	Set $$$ConfigSessionQueueName(..%ConfigName,..%SessionId)=..QueueName()
	$$$sysTRACE("Registered Private Session '"_..%PrivateSessionId_"'")
	Quit $$$OK
}

Method UnRegisterPrivateSession() As %Status
{
	If '..%InPrivateSession Quit $$$OK
	Kill $$$ConfigSessionQueueName(..%ConfigName,..%PrivateSessionId)
    try {
        Set tSC=..Adapter.CloseEventDevice()
    }
    catch {

    }
	 
	Set tSC=##class(Ens.Queue).Delete(..QueueName(),"*") Quit:$$$ISERR(tSC) tSC
	$$$sysTRACE("Unregistered Private Session '"_..%PrivateSessionId_"'")
	Set ..%PrivateSessionId=""
	Set ..%SessionId=""
	Kill $$$JobSessionId
	Quit $$$OK
}

XData MessageMap
{
<MapItems>
<MapItem MessageType="IOP.PrivateSession.Message.Start"><Method>OnMsgPrivateSessionStart</Method></MapItem>
<MapItem MessageType="IOP.PrivateSession.Message.Stop"><Method>OnMsgPrivateSessionStop</Method></MapItem>
<MapItem MessageType="IOP.PrivateSession.Message.Poll"><Method>OnMsgPrivateSessionPoll</Method></MapItem>
</MapItems>
}

Method OnMsgPrivateSessionStart(
	pRequest As IOP.PrivateSession.Message.Start,
	Output pResponse As %Library.Persistent) As %Status
{
    #dim tSC As %Status = $$$OK
    try {
        Set tSC=..RegisterPrivateSession() Quit:$$$ISERR(tSC)
        Set tSC=..OnPrivateSessionStarted(0) Quit:$$$ISERR(tSC)
        Kill %objlasterror Set pResponse=##class(IOP.PrivateSession.Message.Ack).%New()
        If '$IsObject(pResponse) Set tSC=$$$ERROR($$$FailedToNewClass,"IOP.PrivateSession.Message.Ack") Quit
    } catch {
        Set tSC=$$$EnsSystemError
    }
    Quit tSC
}

Method OnMsgPrivateSessionStop(
	pRequest As IOP.PrivateSession.Message.Stop,
	Output pResponse As %Library.Persistent) As %Status
{
    #dim tSC As %Status = $$$OK
    try {
        Set tSC=..UnRegisterPrivateSession() Quit:$$$ISERR(tSC)
        set ..DeferredResponseToken=""
        do ..ReceivedDataQueue.Clear()
        Set tSC=..OnPrivateSessionStopped(0,pRequest.AttachedMessage) Quit:$$$ISERR(tSC)
    } catch {
        Set tSC=$$$EnsSystemError
    }
    Quit tSC
}

Method OnMsgPrivateSessionPoll(
	pPollIn As IOP.PrivateSession.Message.Poll,
	Output pResponse As %Library.Persistent) As %Status
{
    #dim tSC As %Status = $$$OK
    #dim tToken As %String
    try  {
        If ..ReceivedDataQueue.Count() {
            Set pResponse=..ReceivedDataQueue.GetAt(1)
            do ..ReceivedDataQueue.RemoveAt(1)
        } Else {
            Set tSC=..DeferResponse(.tToken) If $$$ISERR(tSC) Quit
            Set ..DeferredResponseToken=tToken
        }
    } catch {
        Set tSC=$$$EnsSystemError
    }
    Quit tSC
}

/// Return an array of connections for drawing lines on the config diagram
ClassMethod OnGetConnections(
	Output pArray As %String,
	pItem As Ens.Config.Item)
{
    Do ##super(.pArray,pItem)
    If pItem.GetModifiedSetting("DuplexTargetConfigName",.tValue) {
        Set tOne=$ZStrip(tValue,"<>W")
        Set:""'=tOne pArray(tOne)=""
    }
}

Method OnPrivateSessionStarted(pSelfGenerated As %Boolean) As %Status
{
	set tSC = $$$OK
	try {
		set response = ..%class."_dispatch_on_private_session_started"($this,pSelfGenerated)
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

Method OnPrivateSessionStopped(
	pSelfGenerated As %Boolean,
	pAttachedMessage As %Persistent = "") As %Status
{
	set tSC = $$$OK
	try {
		set response = ..%class."_dispatch_on_private_session_stopped"($this,pSelfGenerated,pAttachedMessage)
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

Method OnTearDown() As %Status
{
    #dim tSC As %Status = $$$OK
    try {
        If ..%InPrivateSession Set tSC=..StopPrivateSession() Quit:$$$ISERR(tSC)
        do ..%class."_dispatch_on_tear_down"()
    } catch {
        Set tSC=$$$EnsSystemError
    }
    Quit tSC
}

}
