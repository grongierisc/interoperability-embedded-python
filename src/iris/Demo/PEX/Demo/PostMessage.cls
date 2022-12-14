Class dc.Demo.PostMessage Extends Ens.Request
{

Property ToEmailAddress As %String;

Property Found As %String;

Property Post As dc.Reddit.Post;

Storage Default
{
<Data name="PostMessageDefaultData">
<Subscript>"PostMessage"</Subscript>
<Value name="1">
<Value>ToEmailAddress</Value>
</Value>
<Value name="2">
<Value>Post</Value>
</Value>
<Value name="3">
<Value>Found</Value>
</Value>
</Data>
<DefaultData>PostMessageDefaultData</DefaultData>
<Type>%Storage.Persistent</Type>
}

}
