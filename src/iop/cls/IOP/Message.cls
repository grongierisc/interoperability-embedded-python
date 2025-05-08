Class IOP.Message Extends (Ens.MessageBody, %CSP.Page, Ens.VDoc.Interface)
{

Parameter DOCCLASSNAME = "JSON Document";

Parameter DOCCLASSFULLNAME = "JSON Virtual Document";

Parameter DOCSHORTNAME = "JSON";

Parameter BUFFER = 1000000;

Property buffer As %String(MAXLEN = "") [ Calculated, Transient ];

Property classname As %String(MAXLEN = "");

Property jsonObject As %DynamicObject(XMLPROJECTION = "None");

Property json As %String(MAXLEN = "");

Property jsonStream As %Stream.GlobalCharacter [ Internal, Private ];

Property jsonString As %String(MAXLEN = 1000000) [ Internal, Private ];

Property jstr As %Stream.GlobalCharacter [ Internal, Private ];

// for retrocompatibility

Property type As %String(MAXLEN = 6) [ ReadOnly ];

/// Gets the next index in an array
Method GetNextIndex(
	pPath As %String,
	pIndex As %String,
	ByRef pStatus As %Status = {$$$OK}) As %String
{
    Set f=$F(pPath,"()")  If 'f Set pStatus=$$$ERROR($$$EnsErrGeneral,"Can't iterate on no-array type '"_pPath_"'") Quit ""
    if pIndex="" Set pIndex=0
    Set tValue = ..GetValueAt($EXTRACT(pPath, 1, $LENGTH(pPath)-2))
    Set builtins = ##class(%SYS.Python).Builtins()
    if pIndex>=builtins.len(tValue) Quit ""
    Quit pIndex+1
}

Method GetValueAt(
	pPropertyPath As %String = "",
	pFormat As %String,
	Output pStatus As %Status,
	pDummy As %Boolean) As %String
{
    Set pStatus = $$$OK
    Try {
        // Handle standard path queries
        If pPropertyPath = "" Return ""
        
        // pPropertyPath is formatted as :
        // 1. "property1.property2.property3" for nested properties
        // 2. "property1()" for all elements of an array or property1(*)
        // 3. "property1(index).property2" for nested properties within an array
        // 4. "property1(index)" for a specific element of an array

        // Convert pPropertyPath to a a jsonpath
        Set tPath = ..ConvertPath(pPropertyPath)

        Set pyjson = ##class(%SYS.Python).Import("json")
        Set jp = ##class(%SYS.Python).Import("jsonpath_ng")
        Set builtins = ##class(%SYS.Python).Builtins()

		Set tJSON = pyjson.loads(..json)
        Set parser = jp.parse(tPath)
        Set matches = parser.find(tJSON)

        Set tResult = ""
        // Return the first match
        if matches."__len__"() = 1 {
            Set match = matches."__getitem__"(0)
            Set tResult = match."value"
        }
        ElseIf matches."__len__"() > 1 {
            Set tResult = builtins.list()
            For i=0:1:matches."__len__"()-1 {
                Set match = matches."__getitem__"(i)
                Do tResult.append(match."value")
            }
        }

        Return tResult

    } Catch ex {
        Set pStatus = ex.AsStatus()
        Return ""
    }
}

ClassMethod ConvertPath(pPropertyPath As %String) As %String
{
    // Convert pPropertyPath to a jsonpath just by replacing 
    // - '()' with '[*]'
    // - '(index)' with '[index]'
    // - '(' with '[' and ')' with ']'
    // - if index is an integer, replace it with [index-1]
    Set tPath = pPropertyPath
    Set tPath = $Replace(tPath, "()", "[*]")
    Set tPath = $Replace(tPath, "(", "[")
    Set tPath = $Replace(tPath, ")", "]")
    // Process each [] occurrence in the path
    Set tPath = ..ProcessBrackets(tPath)

    Return tPath
}

ClassMethod ProcessBrackets(pPath As %String) As %String
{
    Set tPath = pPath
    Set start = $Find(tPath, "[")
    While start {
        Set end = $Find(tPath, "]", start)
        If 'end Quit  // No matching closing bracket
        
        // Extract the index between [ and ]
        Set tIndex = $Extract(tPath, start, end-2)
        
        // If index is numeric, decrease by 1 (0-based indexing)
        If +tIndex {
            Set newPath = $Extract(tPath, 1, start-1)
            Set newPath = newPath _ (tIndex-1)
            Set newPath = newPath _ $Extract(tPath, end-1, *)
            Set tPath = newPath
        }
        
        // Move past this [] pair for next iteration
        Set start = $Find(tPath, "[", end)
    }
    Return tPath
}

Method CopyValues(
	pSource As Ens.VDoc.Interface,
	pSourcePath As %String,
	pTargetPath As %String,
	pAction As %String,
	pKey As %String,
	pEmptyFieldAsNull As %Boolean = 0,
	pIgnoreMissingSource As %Boolean = 0,
	pGenerateEmptySegments As %Boolean = 0) As %Status
{
    Set tSC = $$$OK
    Try {
        // Get source value
        Set tValue = pSource.GetValueAt(pSourcePath, "String", .tSC, 0)
        Return:$$$ISERR(tSC) tSC

        // Set target value
        Set tSC = ..SetValueAt(tValue, pTargetPath, pAction, pKey)
    } Catch ex {
        Set tSC = ex.AsStatus()
    }
    Return tSC
}

/// Sets a value at the specified property path in the JSON document
/// @param pValue Value to set
/// @param pPropertyPath Path to the property (e.g. "property1.property2" or "array()")
/// @param pAction Action to perform ("set", "append", "remove", "insert")
/// @param pKey Optional key for specialized operations, required for insert
/// @returns %Status
Method SetValueAt(
	pValue As %String = "",
	pPropertyPath As %String = "",
	pAction As %String = "set",
	pKey As %String = "") As %Status
{
    Set tSC = $$$OK
    Try {
        // Validate input parameters
        If pPropertyPath = "" Return $$$ERROR($$$GeneralError, "Property path cannot be empty")
        If '$LISTFIND($LISTBUILD("set","append","remove","insert"), pAction) Return $$$ERROR($$$GeneralError, "Invalid action: "_pAction)
        If (pAction = "insert") && (pKey = "") Return $$$ERROR($$$GeneralError, "Key is required for insert action")

        // Initialize Python objects
        Set pyjson = ##class(%SYS.Python).Import("json")
        Set jp = ##class(%SYS.Python).Import("jsonpath_ng")
        Set builtins = ##class(%SYS.Python).Builtins()

        // Handle append operations
        Set tAppend = (pAction = "append")
        If tAppend, $EXTRACT(pPropertyPath, *-1, *) = "()" {
            Set pPropertyPath = $EXTRACT(pPropertyPath, 1, *-2)
        }

        // Initialize empty JSON if needed
        Set:..json="" ..json = "{}"
        
        // Parse JSON and prepare path
        Set tJSON = pyjson.loads(..json)
        Set tPath = ..ConvertPath(pPropertyPath)
        Set parser = jp.parse(tPath)

        If pAction = "set" {
            // Simple set operation
            Set tJSON = parser."update_or_create"(tJSON, pValue)
        }
        ElseIf pAction = "remove" {
            // Remove operation
            Set matches = parser.find(tJSON)
            If matches."__len__"() > 0 {
                // Not yet implemented
                Set tSC = $$$ERROR($$$GeneralError, "Remove operation not yet implemented")
            }
        }
        ElseIf pAction = "insert" {
            // Handle dictionary insert/update
            Set matches = parser.find(tJSON)
            If matches."__len__"() = 0 {
                // Create new dictionary if path doesn't exist
                Set tDict = builtins.dict()
                Do tDict."__setitem__"(pKey, pValue)
                Set tJSON = parser."update_or_create"(tJSON, tDict)
            }
            Else {
                // Update existing dictionary
                Set tDict = matches."__getitem__"(0)."value"
                Do tDict."__setitem__"(pKey, pValue)
                Set tJSON = parser."update"(tJSON, tDict)
            }
        }
        ElseIf tAppend {
            // Handle append operation
            Set tFindValue = parser."find"(tJSON)
            If tFindValue."__len__"() = 0 {
                // Create new array if path doesn't exist
                Set:(tAppend) tValue = builtins.list()
                Do:tAppend tValue.append(pValue)
                Set tJSON = parser."update_or_create"(tJSON, $Select(tAppend: tValue, 1: pValue))
            }
            Else {
                // Append to existing array
                Do tFindValue."__getitem__"(0)."value".append(pValue)
                Set tJSON = parser."update"(tJSON, tFindValue."__getitem__"(0)."value")
            }
        }

        // Update JSON storage
        Set ..json = pyjson.dumps(tJSON)
        Set ..classname = ..DocType

    }
    Catch ex {
        Set tSC = ex.AsStatus()
        // Log error details
        $$$LOGWARNING("Error in SetValueAt: "_$System.Status.GetErrorText(tSC))
    }
    
    Return tSC
}

Method IsValid() As %Status
{
    Return $$$OK
}

Method Validate(pValidationSpec As %String = "") As %Status
{
    If ..DocType = "" Return $$$ERROR($$$GeneralError, "No DocType specified")
    
    // Validate against stored schema
    Return ##class(IOP.Message.JSONSchema).ValidateJSON(tJSON, ..DocTypeCategory, ..DocTypeName)
}

Method ParentMany(Output pParentsList) As %Integer
{
    Return 0
}

/// Returns a list of available DocTypes by querying the JSONSchema storage.
Query EnumerateDocTypes(
	Category As %String = "",
	IncludeBase As %Boolean = 0) As %Query(CONTAINID = 0, ROWSPEC = "Type:%String")
{
}

ClassMethod EnumerateDocTypesExecute(
	ByRef qHandle As %Binary,
	pName As %String = "",
	IncludeBase As %Boolean) As %Status
{
    Kill qHandle
    Set qHandle = 0
    Set sql = "SELECT Name FROM IOP_Message.JSONSchema"
    If pName '= "" {
        Set sql = sql _ " WHERE Name = ?"
    }

    Set stmt = ##class(%SQL.Statement).%New()
    Set tSC = stmt.%Prepare(sql)
    Quit:$$$ISERR(tSC) tSC

    If pName '= "" {
        Set rs = stmt.%Execute(pName)
    } Else {
        Set rs = stmt.%Execute()
    }
    While rs.%Next() {
        Set qHandle($I(qHandle)) = rs.%Get("Name")
    }
    set qHandle = 0
    Quit $$$OK
}

ClassMethod EnumerateDocTypesFetch(
	ByRef qHandle As %Binary,
	ByRef qRow As %List,
	ByRef AtEnd As %Integer = 0) As %Status
{
    Set qHandle = $O(qHandle(qHandle))
    If qHandle = "" {
        Set qRow = "", AtEnd = 1
        Quit $$$OK
    }
    Set qRow = $LB(qHandle(qHandle))
    Quit $$$OK
}

ClassMethod EnumerateDocTypesClose(ByRef qHandle As %Binary) As %Status
{
    Kill qHandle
    Quit $$$OK
}

/// Returns a list of schema categories from the JSONSchema storage.
Query EnumerateTypeCategories(Standard As %String = "") As %Query(CONTAINID = 0, ROWSPEC = "Category:%String,Description:%String,IsStandard:%Boolean,Base:%String")
{
}

ClassMethod EnumerateTypeCategoriesExecute(
	ByRef qHandle As %Binary,
	pStandard As %String = "") As %Status
{
    Kill qHandle
    Set qHandle = 0
    Set sql = "SELECT Category, Name FROM IOP_Message.JSONSchema"

    Set stmt = ##class(%SQL.Statement).%New()
    Set tSC = stmt.%Prepare(sql)
    Quit:$$$ISERR(tSC) tSC

    Set rs = stmt.%Execute()

    While rs.%Next() {
        Set category = rs.%Get(1)
        // Format: Category, Description, IsStandard, Base
        Set qHandle($I(qHandle)) = $LB(category, "JSON Schema category", "IsStandard", "Base")
    }
    Set qHandle = 0
    Quit $$$OK
}

ClassMethod EnumerateTypeCategoriesFetch(
	ByRef qHandle As %Binary,
	ByRef Row As %List,
	ByRef AtEnd As %Integer = 0) As %Status
{
    Set qHandle = $O(qHandle(qHandle))
    If qHandle = "" {
        Set Row = "", AtEnd = 1
        Quit $$$OK
    }
    Set Row = qHandle(qHandle)
    Quit $$$OK
}

ClassMethod EnumerateTypeCategoriesClose(ByRef qHandle As %Binary) As %Status
{
    Kill qHandle
    Quit $$$OK
}

/// Returns array of properties that make up the <i>contents</i>
/// of this object.<br>
/// This method in implemented within the document class.<br>
/// The content array is in the form:<br>
/// 	pContents(n,"type")="%String"<br>
/// 	pContents(n,"name")="Field"<br>
/// 	pContents(n,"alias")=alias code<br>
/// If pContents(n) is non-zero then the property is a composite type with<br>
/// sub-properties.  The sub-properties are indexed with a similar structure under<br>
///     pContents(n,m) where m is the index of the subtype property.<br>
ClassMethod GetContentArray(
	Output pContents,
	pMode As %String,
	pDocType As %String = "MESSAGE",
	pLevel As %Integer,
	pIncludeBase As %Boolean = 0) As %Status
{
    Set tSC = $$$OK
    Try {
        // Get schema structure
        Set tName = pDocType
        #; Set tName = $Piece(pDocType, ":", 2)

        Set tSC = ##class(IOP.Message.JSONSchema).GetSchema(tName, .json)
        If $$$ISERR(tSC) Return tSC
        set schema = {}.%FromJSON(json)

        $$$ThrowOnError(##class(IOP.Message).SchemaToContents(schema, .tContents))

        Merge @pContents = tContents
    }
    Catch ex {
        Set tSC = ex.AsStatus()
    }
    Return $$$OK
}

/// Convert a JSON schema structure into a contents array format
/// schema: Dynamic object containing the JSON schema
/// Output pContents: Array to store the contents structure
/// Returns: %Status
ClassMethod SchemaToContents(
	schema As %DynamicObject,
	Output pContents) As %Status
{
    Set tSC = $$$OK
    Try {
        Set idx = 0
        Do ..ProcessProperties(schema.properties, .idx, .pContents, schema)
    }
    Catch ex {
        Set tSC = ex.AsStatus()
    }
    Return tSC
}

ClassMethod ProcessProperties(
	properties As %DynamicObject,
	ByRef idx As %Integer,
	Output pContents,
	schema As %DynamicObject) As %Status
{
    Set iterator = properties.%GetIterator()
    While iterator.%GetNext(.key, .value) {
        Set idx = idx + 1
        Do ..HandleProperty(value, .key, idx, .pContents, schema)
    }
    Return $$$OK
}

ClassMethod HandleProperty(
	value As %DynamicObject,
	ByRef key As %String,
	idx As %Integer,
	Output pContents,
	schema As %DynamicObject)
{
    Set type = value.type
    
    If (type = "string") || (type = "number") || (type = "boolean") {
        Do ..HandlePrimitiveType(type, idx, .pContents)
    }
    ElseIf type = "array" {
        Do ..HandleArrayType(value, .key, idx, .pContents, schema)
    }
    ElseIf type = "object" {
        Do ..HandleObjectType(value, idx, .pContents)
    }
    ElseIf $IsObject(value.allOf) {
        Do ..HandleAllOfType(value, key, idx, .pContents, schema)
    }
    ElseIf value.%Get("$ref")'="" {
        Set tDef = schema."$defs".%Get($Piece(value."$ref", "/", *))
        Do ..HandleObjectType(tDef, idx, .pContents)
    }
    Else {
        Set pContents(idx,"type") = type
    }
    
    If type = "array" Set key = key_"()"
    Set pContents = idx
    Set pContents(idx,"name") = key
    Set pContents(idx,"alias") = key
}

ClassMethod HandlePrimitiveType(
	type As %String,
	idx As %Integer,
	Output pContents)
{
    Set pContents(idx,"type") = $Case(type,
        "string": "%String",
        "number": "%Numeric",
        "boolean": "%Boolean")
}

ClassMethod HandleArrayType(
	value As %DynamicObject,
	ByRef key As %String,
	idx As %Integer,
	Output pContents,
	schema As %DynamicObject)
{
    Set pContents(idx,"type") = "()"
    // Handle array as a Handle Property
    Do ..HandleProperty(value.items, key, idx, .pContents, schema)
}

ClassMethod HandleObjectType(
	value As %DynamicObject,
	idx As %Integer,
	Output pContents)
{
    Set pContents(idx,"type") = "object"
    If $IsObject(value.properties) {
        Do ..SchemaToContents(value, .subContents)
        Merge pContents(idx) = subContents
    }
}

ClassMethod HandleAllOfType(
	value As %DynamicObject,
	key As %String,
	idx As %Integer,
	Output pContents,
	schema As %DynamicObject)
{
    Set pContents(idx) = 1 //TODO size of subContents
    Set pContents(idx,"type") = "object"
    Set pContents(idx,"name") = key
    Set pContents(idx,"alias") = key
    
    Set allOfIterator = value.allOf.%GetIterator()
    While allOfIterator.%GetNext(.allOfKey, .allOfValue) {
        If $IsObject(allOfValue."$ref") {
            Do ..SchemaToContents(allOfValue."$ref", .subContents)
        }
        Else {
            Set tDef = schema."$defs".%Get($Piece(allOfValue."$ref","/",*))
            Do ..SchemaToContents(tDef, .subContents)
        }
        Merge pContents(idx) = subContents
    }
}

Method bufferGet()
{
	Quit ..#BUFFER
}

Method %OnNew(classname) As %Status [ Private, ServerOnly = 1 ]
{
	set ..classname = $g(classname)
	Quit $$$OK
}

Method jstrGet()
{
	set rsp = $$$NULLOREF
	// Get as stream no matter what
	if ..type="String" { 
		Set rsp = ##class(%Stream.GlobalCharacter).%New()
		Set sc = rsp.Write(..jsonString)
	}
	elseif ..type="Stream" { 
		set rsp = ..jsonStream
	}
	Quit rsp
}

Method jstrSet(pInput) As %Status
{
	// Set as stream no matter what
	set sc = ..jsonSet(pInput)
	if $$$ISERR(sc) { Quit sc }
	if ..type="String" { 
		set stream = ##class(%Stream.GlobalCharacter).%New()
		Set sc = stream.Write(..jsonString)
		set r%jsonStream = stream
		set i%type = "Stream"
	}
	Quit sc
}

Method jsonGet()
{
	Quit $Case(..type
				, "String":..jsonString
				, "Stream":..jsonStream
				, :$$$NULLOREF)
}

Method jsonSet(pInput) As %Status
{
	Set tOldStream=$Case(..type
				, "String":..jsonString
				, "Stream":..jsonStream
				, :$$$NULLOREF)
	Quit:tOldStream=pInput $$$OK

	If ..type'="" {
		Set:(..type="String") i%jsonString="" 
		Set:(..type="Stream") i%jsonStream=$$$NULLOREF 
		Set i%type = ""
	}

	If $ISOBJECT(pInput) {
		if pInput.%Extends("%Stream.GlobalCharacter") { 
			Set r%jsonStream=pInput, i%type="Stream"
		}
		else { 
			Throw ##class(%Exception.General).%New("Invalid input type, must be a %Stream.GlobalCharacter or a %String")
		}
	}
	Else  {
		if $LENGTH(pInput)>..#BUFFER { 
			// write in a stream
			Set stream = ##class(%Stream.GlobalCharacter).%New()
			for i=1:..#BUFFER:$LENGTH(pInput) {
				Set sc = stream.Write($EXTRACT(pInput,i,(i+..#BUFFER-1)))
				Quit:$$$ISERR(sc)
			}
			Set r%jsonStream=stream, i%type="Stream"
		}
		else {
			Set i%jsonString=pInput, i%type="String"
		}
	}
}

Method GetObjectJson(ByRef atEnd)
{
	set atEnd = 1
	if ..type = "String" {
		set json = ..jsonString
	}
	elseif ..type = "Stream" {
		do ..jsonStream.Rewind()
		set json = ..jsonStream.Read(..#BUFFER)
		set atEnd = ..jsonStream.AtEnd
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
<Value name="4">
<Value>jsonStream</Value>
</Value>
<Value name="5">
<Value>type</Value>
</Value>
<Value name="6">
<Value>jsonString</Value>
</Value>
<Value name="7">
<Value>DocType</Value>
</Value>
<Value name="8">
<Value>TimeCreated</Value>
</Value>
<Value name="9">
<Value>Source</Value>
</Value>
<Value name="10">
<Value>IsMutable</Value>
</Value>
<Value name="11">
<Value>OriginalDocId</Value>
</Value>
</Data>
<Data name="UserValues">
<Attribute>UserValues</Attribute>
<Structure>subnode</Structure>
<Subscript>"IOP.Message.UserValues"</Subscript>
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
