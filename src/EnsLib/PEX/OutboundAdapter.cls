/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class EnsLib.PEX.OutboundAdapter Extends (Ens.OutboundAdapter, EnsLib.PEX.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%remoteClassname:Remote OutboundAdapter,%remoteSettings:Remote OutboundAdapter,%gatewayName:Remote OutboundAdapter,%gatewayHost:Remote OutboundAdapter,%gatewayPort:Remote OutboundAdapter,%gatewayTimeout:Remote OutboundAdapter,%gatewayExtraClasspaths:Remote OutboundAdapter,%useHostConnection:Remote OutboundAdapter";

/// Use Host Connection. If set to true, this adapter will use the connection from the host.
Property %useHostConnection As %Boolean [ Internal ];

Method %DispatchMethod(method As %String, args...) As %ObjectHandle
{
	if $quit {
		quit $method($this.%gatewayProxy,method,args...)
	} else {
		do $method($this.%gatewayProxy,method,args...)
		quit
	}
}

}
