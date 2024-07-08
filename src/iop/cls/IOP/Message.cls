/* Copyright (c) 2021 by InterSystems Corporation.
   Cambridge, Massachusetts, U.S.A.  All rights reserved.
   Confidential property of InterSystems Corporation. */

Class IOP.Message Extends (Ens.MessageBody, %CSP.Page, %XML.Adaptor)
{

Parameter BUFFER = 64000;

Property classname As %String(MAXLEN = "");

Property jsonObject As %DynamicObject(XMLPROJECTION = "None");

Property json As %String(MAXLEN = "");

Property jstr As %Stream.GlobalCharacter [ Internal, Private ];

Method %OnNew(classname) As %Status [ Private, ServerOnly = 1 ]
{
	set ..classname = $g(classname)
	Quit $$$OK
}

Method jsonGet()
{
	QUIT ..GetObjectJson()
}

Method jsonSet(value) As %Status
{
	set ..jsonObject = {}.%FromJSON(value)
	set ..jstr = ##class(%Stream.GlobalCharacter).%New()
    do ..jstr.Write(value)
	return $$$OK
}

Method %DispatchGetProperty(property As %String) As %ObjectHandle
{
	quit $property(..jsonObject,property)
}

Method %DispatchSetProperty(
	property As %String,
	value)
{
	set $property(..jsonObject,property) = value
	quit
}

Method GetObjectJson(ByRef atEnd)
{
	set atEnd = 1
	set json = ..jsonObject.%ToJSON()
	if json = "{}" {
		d ..jstr.Rewind()
		set json = ..jstr.Read(..#BUFFER)
        set atEnd = ..jstr.AtEnd
	}
    QUIT json
}

/// This method is called by the Management Portal to determine the content type that will be returned by the <method>%ShowContents</method> method.
/// The return value is a string containing an HTTP content type.
Method %GetContentType() As %String
{
	Quit "text/html"
}

/// This method is called by the Management Portal to display a portion of the HEAD section of a message-specific content viewer.<br>
Method %ShowContentsHead(pZenOutput As %Boolean = 0)
{
    &html<<script src="https://code.jquery.com/jquery-2.1.1.min.js"></script>> 
	&html<<script>var makeCompleteJSON=function(l,n){for(var r=["{","}","[","]",'"',"'"],t=function(l){for(var n=l.split(""),r=null,t=[],u=0;u<n.length;u++)char=n[u],"'"!=char&&'"'!=char||(null==r?r=char:r==char&&(r=null)),null==r&&":"==char&&t.push(u);return 1==t.length&&t[0]!=n.length-1},u=[],p=null,e=l.split(""),h="",o=-1,a=[],i=0;i<e.length;i++){if($.inArray(e[i],r)>-1){if(0==u.length&&("'"==e[i]||'"'==e[i]))return!1;'"'==p||"'"==p?p==e[i]&&(u.pop(),p=u[u.length-1]):"}"==e[i]&&"{"==p?(u.pop(),a.pop(),p=u[u.length-1],h="",o=-1):"]"==e[i]&&"["==p?(u.pop(),a.pop(),p=u[u.length-1]):(u.push(e[i]),"["==(p=e[i])&&a.push("array"),"{"==p&&(a.push("object"),o=i))}"object"==a[a.length-1]&&(h+=e[i])}if(!n&&o>-1){var s=function(l){for(var n=l.split(""),r=null,u=null,p=[],e=1;e<n.length;e++)"'"!=(r=n[e])&&'"'!=r||(null==u?u=r:u==r&&(u=null)),null==u&&","==r&&p.push(e);var h=[],o=1;for(e=0;e<p.length;e++)h.push($.trim(l.substring(o,p[e]))),o=p[e]+1;h.push($.trim(l.substring(o)));var a=h[h.length-1];return a.split(""),t(a)||h.pop(),"{"+h.join(",")}(h);return l=l.substring(0,o)+s,makeCompleteJSON(l,!0)}for(;u.length>0;)'"'==(p=u.pop())&&(l+='"'),"'"==p&&(l+="'"),"{"==p&&(l+="}"),"["==p&&(l+="]");return l};</script>>  
	&html<<script>!function(e){"use strict";var n=function(n){var a=e("<span />",{"class":"collapser",on:{click:function(){var n=e(this);n.toggleClass("collapsed");var a=n.parent().children(".block"),p=a.children("ul");n.hasClass("collapsed")?(p.hide(),a.children(".dots, .comments").show()):(p.show(),a.children(".dots, .comments").hide())}}});return n&&a.addClass("collapsed"),a},a=function(a,p){var t=e.extend({},{nl2br:!0},p),r=function(e){return e.toString()?e.toString().replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;").replace(/>/g,"&gt;"):""},s=function(n,a){return e("<span />",{"class":a,html:r(n)})},l=function(a,p){switch(e.type(a)){case"object":p||(p=0);var c=e("<span />",{"class":"block"}),d=Object.keys(a).length;if(!d)return c.append(s("{","b")).append(" ").append(s("}","b"));c.append(s("{","b"));var i=e("<ul />",{"class":"obj collapsible level"+p});return e.each(a,function(a,t){d--;var r=e("<li />").append(s('"',"q")).append(a).append(s('"',"q")).append(": ").append(l(t,p+1));-1===["object","array"].indexOf(e.type(t))||e.isEmptyObject(t)||r.prepend(n()),d>0&&r.append(","),i.append(r)}),c.append(i),c.append(s("...","dots")),c.append(s("}","b")),c.append(1===Object.keys(a).length?s("// 1 item","comments"):s("// "+Object.keys(a).length+" items","comments")),c;case"array":p||(p=0);var d=a.length,c=e("<span />",{"class":"block"});if(!d)return c.append(s("[","b")).append(" ").append(s("]","b"));c.append(s("[","b"));var i=e("<ul />",{"class":"obj collapsible level"+p});return e.each(a,function(a,t){d--;var r=e("<li />").append(l(t,p+1));-1===["object","array"].indexOf(e.type(t))||e.isEmptyObject(t)||r.prepend(n()),d>0&&r.append(","),i.append(r)}),c.append(i),c.append(s("...","dots")),c.append(s("]","b")),c.append(1===a.length?s("// 1 item","comments"):s("// "+a.length+" items","comments")),c;case"string":if(a=r(a),/^(http|https|file):\/\/[^\s]+$/i.test(a))return e("<span />").append(s('"',"q")).append(e("<a />",{href:a,text:a})).append(s('"',"q"));if(t.nl2br){var o=/\n/g;o.test(a)&&(a=(a+"").replace(o,"<br />"))}var u=e("<span />",{"class":"str"}).html(a);return e("<span />").append(s('"',"q")).append(u).append(s('"',"q"));case"number":return s(a.toString(),"num");case"undefined":return s("undefined","undef");case"null":return s("null","null");case"boolean":return s(a?"true":"false","bool")}};return l(a)};return e.fn.jsonView=function(n,p){var t=e(this);if(p=e.extend({},{nl2br:!0},p),"string"==typeof n)try{n=JSON.parse(n)}catch(r){}return t.append(e("<div />",{"class":"json-view"}).append(a(n,p))),t}}(jQuery);</script>>
	&html<<style type="text/css">
	.json-view{position:relative}
	.json-view .collapser{width:20px;height:18px;display:block;position:absolute;left:-1.7em;top:-.2em;z-index:5;background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAD1JREFUeNpiYGBgOADE%2F3Hgw0DM4IRHgSsDFOzFInmMAQnY49ONzZRjDFiADT7dMLALiE8y4AGW6LoBAgwAuIkf%2F%2FB7O9sAAAAASUVORK5CYII%3D);background-repeat:no-repeat;background-position:center center;opacity:.5;cursor:pointer}
	.json-view .collapsed{-ms-transform:rotate(-90deg);-moz-transform:rotate(-90deg);-khtml-transform:rotate(-90deg);-webkit-transform:rotate(-90deg);-o-transform:rotate(-90deg);transform:rotate(-90deg)}
	.json-view .bl{display:block;padding-left:20px;margin-left:-20px;position:relative}
	.json-view {font-family:Verdana,sans-serif; font-size: 0.8em;}
	.json-view ul{list-style-type:none;padding-left:2em;border-left:1px dotted;margin:.3em}
	.json-view ul li{position:relative;color:#012E55}
	.json-view .comments,.json-view .dots{display:none;-moz-user-select:none;-ms-user-select:none;-khtml-user-select:none;-webkit-user-select:none;-o-user-select:none;user-select:none}
	.json-view .comments{padding-left:.8em;font-style:italic;color:#888}
	.json-view .bool,.json-view .null,.json-view .num,.json-view .undef{font-weight:700;color:#1A01CC}
	.json-view .str{color:#F79243}
	</style>>
}

/// This method is called by the Management Portal to display a message-specific content viewer.<br>
/// This method displays its content by writing out to the current device.
/// The content should match the type returned by the <method>%GetContentType</method> method.<br>
Method %ShowContents(pZenOutput As %Boolean = 0)
{
	set jsonObject = ..QuoteJS(..GetObjectJson(.atEnd))
	set buffer = ..#BUFFER
    if 'atEnd {
        &html<<div>Warning JSON projection is not comptete, it's truncated, #(buffer)# charaters display</div>>
    }
	// https://github.com/bazh/jquery.json-view
	&html<<div id="element">#(..classname)#</div>>
	&html<<script>$(function() {$('#element').jsonView(makeCompleteJSON(#(jsonObject)#,false));});</script>>
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
