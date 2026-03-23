Include (%occInclude, Ensemble)

Class IOP.Service.Remote.Rest.v1 Extends %CSP.REST
{

XData UrlMap [ XMLNamespace = "http://www.intersystems.com/urlmap" ]
{
<Routes>
<Route Url="/migrate"  Method="PUT"  Call="PutMigrate"/>
<Route Url="/version"  Method="GET"  Call="GetVersion"/>
<Route Url="/status"   Method="GET"  Call="GetStatus"/>
<Route Url="/start"    Method="POST" Call="PostStart"/>
<Route Url="/stop"     Method="POST" Call="PostStop"/>
<Route Url="/kill"     Method="POST" Call="PostKill"/>
<Route Url="/restart"  Method="POST" Call="PostRestart"/>
<Route Url="/update"   Method="POST" Call="PostUpdate"/>
<Route Url="/list"     Method="GET"  Call="GetList"/>
<Route Url="/default"  Method="GET"  Call="GetDefault"/>
<Route Url="/default"  Method="PUT"  Call="PutDefault"/>
<Route Url="/log"      Method="GET"  Call="GetLog"/>
<Route Url="/export"   Method="GET"  Call="GetExport"/>
<Route Url="/test"     Method="POST" Call="PostTest"/>
</Routes>
}

ClassMethod GetVersion() As %Status
{
    Return ..%WriteResponse({"version": "1.0.0", "description": "Interoperability Embedded Python Service API"}.%ToJSON())
}

/// Validate that a namespace exists. Throws on failure.
ClassMethod NamespaceCheck(pNamespace As %String) As %Boolean [ Internal, Private ]
{
	If '##class(%SYS.Namespace).Exists(pNamespace) {
		throw $$$ERROR("NamespaceDoesNotExist")
	}
	Return 1
}

/// Return the namespace from a query parameter, defaulting to USER.
ClassMethod GetNsParam() As %String [ Internal, Private ]
{
	Set ns = %request.Get("namespace")
	Quit $select(ns="":"USER", 1:ns)
}

/// Return the namespace, preferring a body field over the query parameter.
ClassMethod ResolveNs(dyna As %DynamicObject = "") As %String [ Internal, Private ]
{
	Set ns = ""
	If $isobject(dyna) { Set ns = dyna.%Get("namespace") }
	If ns = "" { Set ns = ..GetNsParam() }
	Quit ns
}

ClassMethod GetStatus() As %Status
{
	Try {
		Set ns = ..GetNsParam()
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		$$$ThrowOnError(##class(Ens.Director).GetProductionStatus(.tProdName, .tStatus))
		Set result = {}
		Set result.production = $select(tProdName="":"", 1:tProdName)
		Set result.status = $CASE(tStatus,
			$$$eProductionStateRunning:"running",
			$$$eProductionStateStopped:"stopped",
			$$$eProductionStateSuspended:"suspended",
			$$$eProductionStateTroubled:"troubled",
			:"unknown")
		Return ..%WriteResponse(result.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

ClassMethod PostStart() As %Status
{
	Try {
		Set dyna = {}.%FromJSON(%request.Content)
		Set ns = ..ResolveNs(dyna)
		Set production = dyna.%Get("production")
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		If production = "" { Set production = $Get(^Ens.Configuration("csp","LastProduction")) }
		If production = "" { Throw $$$ERROR("NoProductionSpecified") }
		$$$ThrowOnError(##class(Ens.Director).StartProduction(production))
		Return ..%WriteResponse({"status": "started", "production": (production)}.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

ClassMethod PostStop() As %Status
{
	Try {
		Try { Set dyna = {}.%FromJSON(%request.Content) } Catch { Set dyna = {} }
		Set ns = ..ResolveNs(dyna)
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		$$$ThrowOnError(##class(Ens.Director).StopProduction())
		Return ..%WriteResponse({"status": "stopped"}.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

ClassMethod PostKill() As %Status
{
	Try {
		Try { Set dyna = {}.%FromJSON(%request.Content) } Catch { Set dyna = {} }
		Set ns = ..ResolveNs(dyna)
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		$$$ThrowOnError(##class(Ens.Director).StopProduction(10, 1))
		Return ..%WriteResponse({"status": "killed"}.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

ClassMethod PostRestart() As %Status
{
	Try {
		Try { Set dyna = {}.%FromJSON(%request.Content) } Catch { Set dyna = {} }
		Set ns = ..ResolveNs(dyna)
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		$$$ThrowOnError(##class(Ens.Director).RestartProduction())
		Return ..%WriteResponse({"status": "restarted"}.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

ClassMethod PostUpdate() As %Status
{
	Try {
		Try { Set dyna = {}.%FromJSON(%request.Content) } Catch { Set dyna = {} }
		Set ns = ..ResolveNs(dyna)
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		$$$ThrowOnError(##class(Ens.Director).UpdateProduction())
		Return ..%WriteResponse({"status": "updated"}.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

ClassMethod GetList() As %Status
{
	Try {
		Set ns = ..GetNsParam()
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		Set tRS = ##class(%ResultSet).%New("Ens.Config.Production:ProductionStatus")
		$$$ThrowOnError(tRS.Execute())
		Set result = {}
		While tRS.Next() {
			Set info = {}
			Set info.Status = tRS.Data("Status")
			Set info.LastStartTime = tRS.Data("LastStartTime")
			Set info.LastStopTime = tRS.Data("LastStopTime")
			Set info.AutoStart = ($Get(^Ens.AutoStart) = tRS.Data("Production"))
			Do result.%Set(tRS.Data("Production"), info)
		}
		Return ..%WriteResponse(result.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

ClassMethod GetDefault() As %Status
{
	Try {
		Set ns = ..GetNsParam()
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		Set prod = $Get(^Ens.Configuration("csp","LastProduction"), "")
		Return ..%WriteResponse({"production": (prod)}.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

ClassMethod PutDefault() As %Status
{
	Try {
		Set dyna = {}.%FromJSON(%request.Content)
		Set ns = ..ResolveNs(dyna)
		Set production = dyna.%Get("production")
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		Set ^Ens.Configuration("csp","LastProduction") = production
		Return ..%WriteResponse({"production": (production)}.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

/// GET /log?namespace=USER&top=10&since_id=0
/// Returns log entries as a JSON array, newest last.
/// Use since_id for polling: pass the last seen ID to get only new entries.
ClassMethod GetLog() As %Status
{
	Try {
		Set ns = ..GetNsParam()
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		Set top = %request.Get("top")  If top = "" { Set top = 10 }
		Set sinceId = %request.Get("since_id")

		Set stmt = ##class(%SQL.Statement).%New()
		If sinceId '= "" {
			$$$ThrowOnError(stmt.%Prepare("SELECT ID, ConfigName, Job, MessageId, SessionId, SourceClass, SourceMethod, Text, TimeLogged, Type FROM Ens_Util.Log WHERE ID > ? ORDER BY ID ASC"))
			Set rs = stmt.%Execute(sinceId)
		} Else {
			$$$ThrowOnError(stmt.%Prepare("SELECT TOP ? ID, ConfigName, Job, MessageId, SessionId, SourceClass, SourceMethod, Text, TimeLogged, Type FROM Ens_Util.Log ORDER BY ID DESC"))
			Set rs = stmt.%Execute(top)
		}

		Set result = []
		While rs.%Next() {
			Set entry = {}
			Set entry.id = rs.%Get("ID")
			Set entry."config_name" = rs.%Get("ConfigName")
			Set entry.job = rs.%Get("Job")
			Set entry."message_id" = rs.%Get("MessageId")
			Set entry."session_id" = rs.%Get("SessionId")
			Set entry."source_class" = rs.%Get("SourceClass")
			Set entry."source_method" = rs.%Get("SourceMethod")
			Set entry.text = rs.%Get("Text")
			Set entry."time_logged" = rs.%Get("TimeLogged")
			Set tType = rs.%Get("Type")
			Set entry.type = $CASE(tType, 1:"Assert", 2:"Error", 3:"Warning", 4:"Info", 5:"Trace", 6:"Alert", :"Unknown")
			Do result.%Push(entry)
		}
		Return ..%WriteResponse(result.%ToJSON())
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

/// GET /export?production=MyApp.Production&namespace=USER
/// Returns production definition as JSON (converted from XData XML via xmltodict).
ClassMethod GetExport() As %Status
{
	Try {
		Set ns = ..GetNsParam()
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }
		Set production = %request.Get("production")
		If production = "" { Set production = $Get(^Ens.Configuration("csp","LastProduction"), "") }

		// Read the production XData XML
		Set xdata = ##class(IOP.Utils).ExportProduction(production)
		Do xdata.Rewind()
		Set xml = ""
		While 'xdata.AtEnd { Set xml = xml _ xdata.Read(32000) }

		// Convert to JSON via Python xmltodict
		Set iopUtils = ##class(IOP.Wrapper).Import("iop._utils")
		Set jsonStr = iopUtils."_Utils"."xml_to_json"(xml)
		Return ..%WriteResponse(jsonStr)
	} Catch ex {
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

/// POST /test
/// Body: {"target":"Python.MyOp", "classname":"Python.MyMsg", "body":"{}", "namespace":"USER", "restart":true}
/// If "restart" is true the target component is stopped and restarted before the test message is dispatched. (Default true)
/// Returns: {"classname":"...", "body":"...", "session_id":"..."}
ClassMethod PostTest() As %Status
{
	Try {
		// Capture output to avoid writing directly to the response stream, which would break the JSON format. We'll include captured output in the response.
		set sc = $$BeginCapture^%SYS.Capture(.msg)

		Set dyna = {}.%FromJSON(%request.Content)
		Set target    = dyna.%Get("target")
		Set classname = dyna.%Get("classname")
		Set body      = dyna.%Get("body")
		Set restart   = dyna.%Get("restart")
		If restart = "" { Set restart = 1 }
		Set ns        = ..ResolveNs(dyna)
		If ns '= "" { Do ..NamespaceCheck(ns)  New $NAMESPACE  Set $NAMESPACE = ns }

		// Optionally restart the target component before testing
		If restart {
			$$$ThrowOnError(##class(Ens.Director).EnableConfigItem(target, 0, 1))
			$$$ThrowOnError(##class(Ens.Director).EnableConfigItem(target, 1, 1))
		}

		// Normalize body: if it arrived as a JSON object, serialize it to a string
		If $isobject(body) { Set body = body.%ToJSON() }

		// Build the request message
		If classname '= "" {
			Set message = ##class(IOP.Message).%New()
			Set message.classname = classname
			Set message.json = $select(body="":"{}", 1:body)
		} Else {
			Set message = ##class(Ens.Request).%New()
		}

		// Dispatch to the target component
		Set response = ##class(IOP.Utils).dispatchTestComponent(target, message)

		// Build result
		Set result = {}
		If $isobject(response) {
			
			If response.%IsA("IOP.Message") {
				Set result.body = response.GetObjectJson(.atEnd)
				set result.classname = response.classname
				Set result.truncated = 'atEnd
			} 
			Else {
				Set result.classname = response.%ClassName(1)
				// Use the ObjectScript XML Serializer so arbitrary objects and collections are captured.
				Try {
					Set xmlWriter = ##class(%XML.Writer).%New()
					Set xmlStream = ##class(%Stream.TmpCharacter).%New()
					$$$ThrowOnError(xmlWriter.OutputToStream(xmlStream))
					$$$ThrowOnError(xmlWriter.RootObject(response))
					Do xmlStream.Rewind()
					Set body = ""
					While 'xmlStream.AtEnd { Set body = body _ xmlStream.Read(32000) }
					Set result.body = body
				} Catch {
					Set result.body = ""
				}
			}
		}
		set sc = $$EndCapture^%SYS.Capture(msg,.msgArray)
		Return ..%WriteResponse(result.%ToJSON())
	} Catch ex {
		set sc = $$EndCapture^%SYS.Capture(msg,.msgArray)
		Return ..%WriteErrorResponse(ex.DisplayString())
	}
}

/// Write a successful JSON response.
ClassMethod %WriteResponse(pJson As %String) As %Status [ Internal, Private ]
{
	Set %response.ContentType = "application/json"
	Set %response.Status = "200 OK"
	Write pJson
	Quit $$$OK
}

/// Write an error JSON response.
ClassMethod %WriteErrorResponse(
	pMessage As %String,
	pStatus As %Integer = 500) As %Status [ Internal, Private ]
{
	Set %response.ContentType = "application/json"
	Set %response.Status = pStatus_" Error"
	Write {"error": (pMessage)}.%ToJSON()
	Quit $$$OK
}

ClassMethod PutMigrate() As %DynamicObject
{
	Try {
		// Get the request body
		set dyna = {}.%FromJSON(%request.Content)
		set body = dyna.%Get("body")
		set namespace = ..ResolveNs(dyna)
		set targetDirectory = dyna.%Get("remote_folder")
		set packageName = dyna.%Get("package")
		// check for namespace existence and user permissions against namespace
		If '..NamespaceCheck(namespace) {
			Return ""
		}
		New $NAMESPACE
		Set $NAMESPACE = namespace

		
		//Create directory for custom packages
		If targetDirectory '= "" {
			If '##class(%Library.File).DirectoryExists(targetDirectory) {
				If '##class(%Library.File).CreateDirectory(targetDirectory) {
					$$$ThrowStatus($$$ERROR($$$DirectoryCannotCreate, targetDirectory))
				}
			}
		}
		Else {
			// Set targetDirectory to the CODE DATABASE directory
			do ##class(%SYS.Namespace).GetAllNSInfo(namespace,.info)
			Set targetDirectory = info("RoutineDB","Directory")
		}
		
		Set packagePath = ##class(%Library.File).NormalizeDirectory(packageName, targetDirectory)
		// If the package already exists then we must be meaning to re-load it. Delete files/directory/metadata and recreate fresh.
		If ##class(%Library.File).DirectoryExists(packagePath) {
			If '##class(%Library.File).RemoveDirectoryTree(packagePath) {
				$$$ThrowStatus($$$ERROR($$$DirectoryPermission , packagePath))
			}
		}
		If '##class(%Library.File).CreateDirectory(packagePath) {
			$$$ThrowStatus($$$ERROR($$$DirectoryCannotCreate, packagePath))
		}

		//Unpack JSON objects		
		Set iterator = body.%GetIterator()
		While iterator.%GetNext(.key , .fileObject ) {
			// If fileObject.name has '/' then it is a path, we need to normalize it
			Set fileName = ##class(%Library.File).NormalizeFilename(fileObject.name,packagePath)
			do ##class(%Library.File).CreateDirectoryChain(##class(%Library.File).GetDirectory(fileName))
			Set fileStream = ##class(%Stream.FileCharacter).%New()
			Set fileStream.TranslateTable = "UTF8"
			$$$ThrowOnError(fileStream.LinkToFile(fileName))
			Do fileStream.Write(fileObject.data)
			$$$ThrowOnError(fileStream.%Save())
		}

		//Do the iop migration

		set iopUtils = ##class(IOP.Wrapper).Import("iop._utils")
    	do iopUtils."_Utils".migrate(##class(%Library.File).NormalizeFilename("settings.py", packagePath))
	}
	Catch ex {
		$$$ThrowOnError(ex.AsStatus())
	}


	return $$$OK
}

}
