Class dc.Reddit.Post Extends (%Persistent, %JSON.Adaptor, %XML.Adaptor)
{

Parameter %JSONIGNOREINVALIDFIELD = 1;

Property OriginalJSON As %String(%JSONINCLUDE = "none", MAXLEN = 3000000);

Property Title As %String(%JSONFIELDNAME = "title", MAXLEN = 255);

Property Selftext As %String(%JSONFIELDNAME = "selftext", MAXLEN = 3000000);

Property Author As %String(%JSONFIELDNAME = "author", MAXLEN = 255);

Property Url As %String(%JSONFIELDNAME = "url", MAXLEN = 255);

Property CreatedUTC As %Float(%JSONFIELDNAME = "created_utc");

Storage Default
{
<Data name="PostDefaultData">
<Value name="1">
<Value>%%CLASSNAME</Value>
</Value>
<Value name="2">
<Value>OriginalJSON</Value>
</Value>
<Value name="3">
<Value>selftext</Value>
</Value>
<Value name="4">
<Value>title</Value>
</Value>
<Value name="5">
<Value>author</Value>
</Value>
<Value name="6">
<Value>url</Value>
</Value>
<Value name="7">
<Value>created_utc</Value>
</Value>
<Value name="8">
<Value>Title</Value>
</Value>
<Value name="9">
<Value>Selftext</Value>
</Value>
<Value name="10">
<Value>Author</Value>
</Value>
<Value name="11">
<Value>Url</Value>
</Value>
<Value name="12">
<Value>CreatedUTC</Value>
</Value>
</Data>
<DataLocation>^dc.Reddit.PostD</DataLocation>
<DefaultData>PostDefaultData</DefaultData>
<IdLocation>^dc.Reddit.PostD</IdLocation>
<IndexLocation>^dc.Reddit.PostI</IndexLocation>
<StreamLocation>^dc.Reddit.PostS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
