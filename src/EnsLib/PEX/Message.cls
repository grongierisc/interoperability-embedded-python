/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class EnsLib.PEX.Message Extends Ens.MessageBody
{

Property %classname As %String;

Property %jsonObject As %DynamicObject(XMLPROJECTION = "NONE");

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


}
