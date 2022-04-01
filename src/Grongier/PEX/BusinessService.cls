/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class Grongier.PEX.BusinessService Extends (Ens.BusinessService, Grongier.PEX.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%classname:Python BusinessService,%module:Python BusinessService,%settings:Python BusinessService,%classpaths:Python BusinessService";

Method dispatchProcessInput(pInput As %RegisteredObject) As %RegisteredObject
{
	set tSC = ..ProcessInput(pInput,.tOutput)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit tOutput
}

Method OnProcessInput(request As %RegisteredObject, Output response As %RegisteredObject) As %Status
{
	set tSC = $$$OK
	try {
		try {
			set ..%class."_WaitForNextCallInterval" = ..%WaitForNextCallInterval
		} catch {}
		if $isObject(request),request.%IsA("Grongier.PEX.Message") set request = ..serialize(request)
		set response = ..%class."_dispatchOnProcessInput"(request)

		try {
			set ..%WaitForNextCallInterval = ..%class."_WaitForNextCallInterval"
		} catch {}
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

}
