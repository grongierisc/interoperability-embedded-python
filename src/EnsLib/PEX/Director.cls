/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class EnsLib.PEX.Director [ Inheritance = right, ProcedureBlock, System = 4 ]
{

ClassMethod dispatchCreateBusinessService(pTargetDispatchName As %String) As Ens.BusinessService
{
	set tSC = ##class(Ens.Director).CreateBusinessService(pTargetDispatchName,.service)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit service
}

}
