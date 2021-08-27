/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class Grongier.PEX.Message Extends Ens.MessageBody
{

Property %classname As %String;

Property %jsonObject As %DynamicObject;

Property %json As %String [ Calculated ];

Method %OnNew(classname) As %Status [ Private, ServerOnly = 1 ]
{
	set ..%classname = $g(classname)
	Quit $$$OK
}

Method %jsonGet()
{
	quit ..%jsonObject.%ToJSON()
}

Method %DispatchGetProperty(property As %String) As %ObjectHandle
{
	quit $property(..%jsonObject,property)
}

Method %DispatchSetProperty(property As %String, value)
{
	set $property(..%jsonObject,property) = value
	quit
}

Storage Default
{
<Data name="%jsonObject">
<Attribute>%jsonObject</Attribute>
<Structure>node</Structure>
<Subscript>"Grongier.PEX.Message.%jsonObject"</Subscript>
</Data>
<Data name="MessageDefaultData">
<Subscript>"Message"</Subscript>
<Value name="1">
<Value>%classname</Value>
</Value>
</Data>
<DefaultData>MessageDefaultData</DefaultData>
<Type>%Storage.Persistent</Type>
}

}
