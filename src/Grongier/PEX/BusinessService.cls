/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class Grongier.PEX.BusinessService Extends (Ens.BusinessService, Grongier.PEX.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter ADAPTER = "Ens.InboundAdapter";

Parameter SETTINGS = "%classname:Python BusinessOperation,%module:Python BusinessOperation,%settings:Python BusinessOperation,%classpaths:Python BusinessOperation";

ClassMethod dispatchProcessInput(host As %RegisteredObject, pInput As %RegisteredObject) As %RegisteredObject
{
	// dispatchProcessInput is a classmethod because it can be called on a BusinessService object that is not PEX enabled
	set tSC = host.ProcessInput(pInput,.tOutput)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit tOutput
}

Method OnProcessInput(request As %RegisteredObject, Output response As %RegisteredObject) As %Status
{
	set tSC = $$$OK
	try {
		do ..Connect()
		try {
			set ..%class."_WaitForNextCallInterval" = ..%WaitForNextCallInterval
		} catch {}
		set response = ..%class.OnProcessInput(request)
		try {
			set ..%WaitForNextCallInterval = ..%class."_WaitForNextCallInterval"
		} catch {}
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

}
