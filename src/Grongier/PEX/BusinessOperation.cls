/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class Grongier.PEX.BusinessOperation Extends (Ens.BusinessOperation, Grongier.PEX.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%classname:Python BusinessOperation,%module:Python BusinessOperation,%settings:Python BusinessOperation,%classpaths:Python BusinessOperation";

Method OnMessage(request As %Library.Persistent, Output response As %Library.Persistent) As %Status
{
	set tSC = $$$OK
	try {
		if $isObject(request),request.%IsA("EnsLib.PEX.Message") set request = ..serialize(request)
		set response = ..%class."_dispatchOnMessage"(request)
		if response'="",$isObject(response)=0 set response = ..deserialize(response)
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

/// Test Methode
ClassMethod Test() As %Status
{
	Set sc = $$$OK
	set mybo = ..%New("mybo")
	set mybo.%classpaths = "/irisdev/app/src/python/demo/:/usr/irissys/mgr/python/"
	set mybo.%module = "MyBusinessOperation"
	set mybo.%classname = "MyBusinessOperation"
	set sc = mybo.OnInit()
	Return sc
}

}
