Class IOP.Message.JSONSchema Extends %Persistent
{

Property Name As %String;

Property Category As %String;

Property JSONSchema As %String(MAXLEN = "");

Index NameIndex On Name [ IdKey, Unique ];

/// Import a JSON Schema from file
ClassMethod ImportFromFile(
	pFileName As %String,
	pCategory As %String = "",
	pName As %String) As %Status
{
    Set pStatus = $$$OK
    Try {
        If '##class(%File).Exists(pFileName) {
            Set pStatus = $$$ERROR($$$GeneralError, "File not found")
            Return pStatus
        }
        Set tFile = ##class(%File).%New(pFileName)
        $$$ThrowOnError(tFile.Open("R"))
        Set tSchema = ""
        While 'tFile.AtEnd {
            Set tSchema = tSchema _ tFile.ReadLine()
        }
        Set pStatus = ..Import(tSchema, pCategory, pName)
    } Catch ex {
        Set pStatus = ex.AsStatus()
    }
    Return pStatus
}

/// Store the JSON Schema in this object
ClassMethod Import(
	pSchema As %String,
	pCategory As %String = "",
	pName As %String) As %Status
{
    Set pStatus = $$$OK
    Try {
        if ##class(IOP.Message.JSONSchema).%ExistsId(pName) {
            Set tThis = ##class(IOP.Message.JSONSchema).%OpenId(pName)
            Set tThis.Category = pCategory
            Set tThis.JSONSchema = pSchema
            $$$ThrowOnError(tThis.%Save())
        } Else {
            Set tThis = ##class(IOP.Message.JSONSchema).%New()
            Set tThis.Name = pName
            Set tThis.Category = pCategory
            Set tThis.JSONSchema = pSchema
            $$$ThrowOnError(tThis.%Save())
        }
    } Catch ex {
        Set pStatus = ex.AsStatus()
    }
    Quit pStatus
}

/// Get a stored schema by category and name
ClassMethod GetSchema(
	pName As %String = "",
	Output pSchema As %String) As %Status
{
    Set pStatus = $$$OK
    Try {
        Set tSql = "SELECT JSONSchema FROM IOP_Message.JSONSchema WHERE Name = ?"
        Set tStatement = ##class(%SQL.Statement).%New()
        Do tStatement.%Prepare(tSql)
        set rs = tStatement.%Execute(pName)
        If rs.%Next() {
            Set pSchema = rs.%Get("JSONSchema")
        } Else {
            Set pStatus = $$$ERROR($$$GeneralError, "Schema not found")
        }
    } Catch ex {
        Set pStatus = ex.AsStatus()
    }
    Return pStatus
}

/// Validate JSON data against a stored schema
ClassMethod ValidateJSONSchema(
	pJSON As %String,
	pName As %String) As %Status
{
    Set tSC = $$$OK
    Try {
        Set tSchema = ""
        Set tSC = ..GetSchema(pName, .tSchema)
        If $$$ISERR(tSC) Return tSC
        // Validate JSON data against schema
        // To be implemented
        Set tSC = $$$OK
    } Catch ex {
        Set tSC = ex.AsStatus()
    }
    Return tSC
}

Storage Default
{
<Data name="JSONSchemaDefaultData">
<Value name="1">
<Value>%%CLASSNAME</Value>
</Value>
<Value name="2">
<Value>JSONSchema</Value>
</Value>
<Value name="3">
<Value>Category</Value>
</Value>
</Data>
<DataLocation>^IOP.Message.JSONSchemaD</DataLocation>
<DefaultData>JSONSchemaDefaultData</DefaultData>
<IdLocation>^IOP.Message.JSONSchemaD</IdLocation>
<IndexLocation>^IOP.Message.JSONSchemaI</IndexLocation>
<StreamLocation>^IOP.Message.JSONSchemaS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
