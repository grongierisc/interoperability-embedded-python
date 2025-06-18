/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.Generator.Message.Stop Extends (%Persistent, Ens.Util.MessageBodyMethods) [ ClassType = persistent, Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter DOMAIN = "PrivateSession";

/// From 'Ens.Util.MessageBodyMethods'
Method %ShowContents(pZenOutput As %Boolean = 0)
{

		Write $$$Text("(session-stop)")
}

Storage Default
{
<Data name="StopDefaultData">
<Value name="1">
<Value>%%CLASSNAME</Value>
</Value>
</Data>
<DataLocation>^IOP.Generator.Message.StopD</DataLocation>
<DefaultData>StopDefaultData</DefaultData>
<IdLocation>^IOP.Generator.Message.StopD</IdLocation>
<IndexLocation>^IOP.Generator.Message.StopI</IndexLocation>
<StreamLocation>^IOP.Generator.Message.StopS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
