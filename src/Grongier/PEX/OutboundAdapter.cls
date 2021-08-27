/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class Grongier.PEX.OutboundAdapter Extends (Ens.OutboundAdapter, Grongier.PEX.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%classname:Python InboundAdapter,%module:Python InboundAdapter,%settings:Python InboundAdapter,%classpaths:Python InboundAdapter";

/// Use Host Connection. If set to true, this adapter will use the connection from the host.
Property %useHostConnection As %Boolean [ Internal ];

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
