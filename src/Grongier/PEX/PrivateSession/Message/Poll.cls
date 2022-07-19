/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

/// This class is a DICOM framework class
Class Grongier.PEX.PrivateSession.Message.Poll Extends (%Persistent, Ens.Util.MessageBodyMethods) [ ClassType = persistent, Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter DOMAIN = "PrivateSession";

/// From 'Ens.Util.MessageBodyMethods'
Method %ShowContents(pZenOutput As %Boolean = 0)
{
	Write $$$Text("(poll-data)")
}

Storage Default
{
<Data name="PollDefaultData">
<Value name="1">
<Value>%%CLASSNAME</Value>
</Value>
</Data>
<DataLocation>^Grongier.PEX.PrivateS9756.PollD</DataLocation>
<DefaultData>PollDefaultData</DefaultData>
<IdLocation>^Grongier.PEX.PrivateS9756.PollD</IdLocation>
<IndexLocation>^Grongier.PEX.PrivateS9756.PollI</IndexLocation>
<StreamLocation>^Grongier.PEX.PrivateS9756.PollS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
