/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.PrivateSession.Message.Start Extends (%Persistent, Ens.Util.MessageBodyMethods) [ ClassType = persistent, Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter DOMAIN = "PrivateSession";

/// From 'Ens.Util.MessageBodyMethods'
Method %ShowContents(pZenOutput As %Boolean = 0)
{
	Write $$$Text("(session-start)")
}

Storage Default
{
<Data name="StartDefaultData">
<Value name="1">
<Value>%%CLASSNAME</Value>
</Value>
</Data>
<DataLocation>^IOP.PrivateSession.M6AEC.StartD</DataLocation>
<DefaultData>StartDefaultData</DefaultData>
<IdLocation>^IOP.PrivateSession.M6AEC.StartD</IdLocation>
<IndexLocation>^IOP.PrivateSession.M6AEC.StartI</IndexLocation>
<StreamLocation>^IOP.PrivateSession.M6AEC.StartS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
