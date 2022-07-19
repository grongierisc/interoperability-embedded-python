/* Copyright (c) 2022 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

/// This class is a DICOM framework class
Class Grongier.PEX.PrivateSession.Message.Ack Extends (%Persistent, Ens.Util.MessageBodyMethods) [ ClassType = persistent, Inheritance = right, ProcedureBlock, System = 4 ]
{

Parameter DOMAIN = "PrivateSession";

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
<DataLocation>^Grongier.PEX.PrivateSe9756.AckD</DataLocation>
<DefaultData>AckDefaultData</DefaultData>
<IdLocation>^Grongier.PEX.PrivateSe9756.AckD</IdLocation>
<IndexLocation>^Grongier.PEX.PrivateSe9756.AckI</IndexLocation>
<StreamLocation>^Grongier.PEX.PrivateSe9756.AckS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
