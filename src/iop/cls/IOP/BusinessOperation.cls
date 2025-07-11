/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.BusinessOperation Extends (Ens.BusinessOperation, IOP.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%classname:Python BusinessOperation,%module:Python BusinessOperation,%settings:Python BusinessOperation,%classpaths:Python BusinessOperation";

Method MessageHandler(
	pRequest As %Library.Persistent,
	Output pResponse As %Library.Persistent) As %Status
{
	set tSC = $$$OK
	try {
		set pResponse = ..%class."_dispatch_on_message"(pRequest)
	} catch ex {
		set tSC = ..DisplayTraceback(ex)
	}
	quit tSC
}

Method OnKeepalive(pStatus As %Status = {$$$OK}) As %Status
{
	set tSC = $$$OK
	try {
		$$$ThrowOnError(##super(pStatus))
		do ..%class."on_keepalive"()
	} catch ex {
		set tSC = ..DisplayTraceback(ex)
	}
	quit tSC
}

}
