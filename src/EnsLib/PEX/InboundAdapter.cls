/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class EnsLib.PEX.InboundAdapter Extends (Ens.InboundAdapter, EnsLib.PEX.Common) [ Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter SETTINGS = "%remoteClassname:Remote InboundAdapter,%remoteSettings:Remote InboundAdapter,%gatewayName:Remote InboundAdapter,%gatewayHost:Remote InboundAdapter,%gatewayPort:Remote InboundAdapter,%gatewayTimeout:Remote InboundAdapter,%gatewayExtraClasspaths:Remote InboundAdapter,%useHostConnection:Remote InboundAdapter";

/// Use Host Connection. If set to true, this adapter will use the connection from the host.
Property %useHostConnection As %Boolean [ Internal ];

Method OnTask() As %Status
{
	set tSC = $$$OK
	try {
		set tSC = ..CheckGatewayConnection() quit:$$$ISERR(tSC)
		do ..%gatewayProxy.OnTask()
	} catch ex {
		set tSC = ex.AsStatus()
		do ..CheckGatewayDisconnection()
	}
	quit tSC
}

}
