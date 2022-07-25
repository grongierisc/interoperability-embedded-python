/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

/// This class is a DICOM framework class
Class Grongier.PEX.PrivateSession.Message.Stop Extends (%Persistent, Ens.Util.MessageBodyMethods) [ ClassType = persistent, Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter DOMAIN = "PrivateSession";

/// The message body
Property AttachedMessage As %Persistent(CLASSNAME = 1);

/// From 'Ens.Util.MessageBodyMethods'
Method %ShowContents(pZenOutput As %Boolean = 0)
{
	If $IsObject(..AttachedMessage) {
		Write $$$FormatText($$$Text("(session-stop) with AttachedMessage [%1] "),$classname(..AttachedMessage))
	} Else {
		Write $$$Text("(session-stop)")
	}
}

Method %OnNew(initvalue As %RegisteredObject) As %Status [ Private, ProcedureBlock = 1, ServerOnly = 1 ]
{
	Set ..AttachedMessage=initvalue
	Quit $$$OK
}

Storage Default
{
<Data name="StopDefaultData">
<Value name="1">
<Value>%%CLASSNAME</Value>
</Value>
<Value name="2">
<Value>AttachedMessage</Value>
</Value>
</Data>
<DataLocation>^Grongier.PEX.PrivateS9756.StopD</DataLocation>
<DefaultData>StopDefaultData</DefaultData>
<IdLocation>^Grongier.PEX.PrivateS9756.StopD</IdLocation>
<IndexLocation>^Grongier.PEX.PrivateS9756.StopI</IndexLocation>
<StreamLocation>^Grongier.PEX.PrivateS9756.StopS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
