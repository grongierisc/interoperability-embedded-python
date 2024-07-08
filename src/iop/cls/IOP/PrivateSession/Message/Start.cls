/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

/// This class is a DICOM framework class
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
<DataLocation>^IOP.Private9756.StartD</DataLocation>
<DefaultData>StartDefaultData</DefaultData>
<IdLocation>^IOP.Private9756.StartD</IdLocation>
<IndexLocation>^IOP.Private9756.StartI</IndexLocation>
<StreamLocation>^IOP.Private9756.StartS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
