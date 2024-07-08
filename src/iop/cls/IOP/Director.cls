/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Include (%occInclude, Ensemble)

Class IOP.Director [ Inheritance = right, ProcedureBlock, System = 4 ]
{

ClassMethod dispatchCreateBusinessService(pTargetDispatchName As %String) As Ens.BusinessService
{
	set tSC = ##class(Ens.Director).CreateBusinessService(pTargetDispatchName,.service)
	if $$$ISERR(tSC) throw ##class(%Exception.StatusException).CreateFromStatus(tSC)
	quit service
}

ClassMethod dispatchListProductions() As %String
{
	// Loop over the productions in this namespace
	Set tRS = ##class(%ResultSet).%New("Ens.Config.Production:ProductionStatus")
	If '$IsObject(tRS) Set tSC = %objlasterror Quit
	
	Set tSC = tRS.Execute()
	Quit:$$$ISERR(tSC)
	
	set tDict = ##class(%SYS.Python).Import("builtins").dict()

	While (tRS.Next()) {
		Set tProduction = tRS.Data("Production")
		Set tInfo = ##class(%SYS.Python).Import("builtins").dict()
		do tInfo."__setitem__"("Status",tRS.Data("Status"))
		do tInfo."__setitem__"("LastStartTime",tRS.Data("LastStartTime"))
		do tInfo."__setitem__"("LastStopTime",tRS.Data("LastStopTime"))
		do tInfo."__setitem__"("AutoStart",$G(^Ens.AutoStart)=tProduction)
		do tDict."__setitem__"(tProduction,tInfo)
	}

	Kill tRS

	return tDict
}

ClassMethod StatusProduction() As %String
{
	Set sc = $$$OK
	Set tInfo = ##class(%SYS.Python).Import("builtins").dict()
	$$$ThrowOnError(##class(Ens.Director).GetProductionStatus(.tProdName,.tStatus))
	do tInfo."__setitem__"("Production",tProdName)
	do tInfo."__setitem__"("Status",$CASE(tStatus,$$$eProductionStateRunning:"running",
												$$$eProductionStateStopped:"stopped",
												$$$eProductionStateSuspended:"suspended",
												$$$eProductionStateTroubled:"toubled",
												:"unknown"))
	Return tInfo
}

}
