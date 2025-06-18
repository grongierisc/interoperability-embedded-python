/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.Generator.Message.Ack Extends (%Persistent, Ens.Util.MessageBodyMethods) [ ClassType = persistent, Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter DOMAIN = "Generator";

/// From 'Ens.Util.MessageBodyMethods'
Method %ShowContents(pZenOutput As %Boolean = 0)
{
	Write $$$Text("(session-ack)")
}

Storage Default
{
<Data name="AckDefaultData">
<Value name="1">
<Value>%%CLASSNAME</Value>
</Value>
</Data>
<DataLocation>^IOP.Generator.Message.AckD</DataLocation>
<DefaultData>AckDefaultData</DefaultData>
<IdLocation>^IOP.Generator.Message.AckD</IdLocation>
<IndexLocation>^IOP.Generator.Message.AckI</IndexLocation>
<StreamLocation>^IOP.Generator.Message.AckS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
