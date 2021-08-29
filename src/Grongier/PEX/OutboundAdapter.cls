/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class Grongier.PEX.OutboundAdapter Extends (Ens.OutboundAdapter, Grongier.PEX.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%classname:Python OutboundAdapter,%module:Python OutboundAdapter,%settings:Python OutboundAdapter,%classpaths:Python OutboundAdapter";

Method %DispatchMethod(method As %String, args...) As %ObjectHandle
{
	if $quit {
		quit $method($this.%class,method,args...)
	} else {
		do $method($this.%class,method,args...)
		quit
	}
}

}
