/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.PickleMessage Extends (Ens.MessageBody, %CSP.Page)
{

Property classname As %String(MAXLEN = "");

Property jstr As %Stream.GlobalCharacter [ Internal, Private ];

Method %OnNew(classname) As %Status [ Private, ServerOnly = 1 ]
{
	set ..classname = $g(classname)
	Quit $$$OK
}

/// This method is called by the Management Portal to determine the content type that will be returned by the <method>%ShowContents</method> method.
/// The return value is a string containing an HTTP content type.
Method %GetContentType() As %String
{
	Quit "text/html"
}

/// This method is called by the Management Portal to display a message-specific content viewer.<br>
/// This method displays its content by writing out to the current device.
/// The content should match the type returned by the <method>%GetContentType</method> method.<br>
Method %ShowContents(pZenOutput As %Boolean = 0)
{
	// https://github.com/bazh/jquery.json-view
	&html<<div id="element">#(..classname)#</div>>
	&html<<div>Pickle Pyhton Message can't be displayed</div>>
}

Storage Default
{
<Data name="MessageDefaultData">
<Subscript>"Message"</Subscript>
<Value name="1">
<Value>classname</Value>
</Value>
<Value name="2">
<Value>json</Value>
</Value>
<Value name="3">
<Value>jstr</Value>
</Value>
</Data>
<Data name="jsonObject">
<Attribute>jsonObject</Attribute>
<Structure>node</Structure>
<Subscript>"IOP.Message.jsonObject"</Subscript>
</Data>
<DefaultData>MessageDefaultData</DefaultData>
<Type>%Storage.Persistent</Type>
}

}
