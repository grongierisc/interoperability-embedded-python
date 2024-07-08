/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.OutboundAdapter Extends (Ens.OutboundAdapter, IOP.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Property KeepaliveInterval As %Numeric [ InitialExpression = 0 ];

Parameter SETTINGS = "KeepaliveInterval:Python CallInterval,%classname:Python OutboundAdapter,%module:Python OutboundAdapter,%settings:Python OutboundAdapter,%classpaths:Python OutboundAdapter";

Method %DispatchMethod(
	method As %String,
	args...) As %ObjectHandle
{
	if $quit {
		quit $method($this.%class,method,args...)
	} else {
		do $method($this.%class,method,args...)
		quit
	}
}

Method OnKeepalive(pStatus As %Status = {$$$OK}) As %Status
{
	set tSC = $$$OK
	try {
		$$$ThrowOnError(##super(pStatus))
		do ..%class."on_keepalive"()
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

}
