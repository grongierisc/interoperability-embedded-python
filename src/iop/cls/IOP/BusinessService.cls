/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.BusinessService Extends (Ens.BusinessService, IOP.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%classname:Python BusinessService,%module:Python BusinessService,%settings:Python BusinessService,%classpaths:Python BusinessService";

Method dispatchProcessInput(pInput As %RegisteredObject) As %RegisteredObject
{
	
	quit ..%class."on_process_input"(pInput)
}

Method OnProcessInput(
	request As %RegisteredObject,
	Output response As %RegisteredObject) As %Status
{
	set tSC = $$$OK
	try {
		try {
			set ..%class."_wait_for_next_call_interval" = ..%WaitForNextCallInterval
		} catch {}
		set response = ..%class."_dispatch_on_process_input"(request)
		try {
			set ..%WaitForNextCallInterval = ..%class."_wait_for_next_call_interval"
		} catch {}
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

}
