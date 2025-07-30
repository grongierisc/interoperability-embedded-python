Class IOP.Service.Remote.Rest.v1 Extends %CSP.REST
{

XData UrlMap [ XMLNamespace = "http://www.intersystems.com/urlmap" ]
{
<Routes>
<Route Url="/migrate"                        Method="PUT" Call="PutMigrate"/>
<Route Url="/version"                        Method="GET" Call="GetVersion"/>
</Routes>
}

ClassMethod GetVersion() As %String
{
    // Return the version of the IOP service
    Return {
		"version": "1.0.0",
		"description": "Interoperability Embedded Python Service API"
	}.%ToJSON()
}

ClassMethod NamespaceCheck(pNamespace As %String) As %Boolean [ Internal, Private ]
{
	If '##class(%SYS.Namespace).Exists(pNamespace) {
		throw $$$ERROR("NamespaceDoesNotExist")
	}
	Return 1
}

ClassMethod PutMigrate() As %DynamicObject
{
	Try {
		// Get the request body
		set dyna = {}.%FromJSON(%request.Content)
		set body = dyna.%Get("body")
		set namespace = dyna.%Get("namespace")
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
