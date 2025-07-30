# This module provides a REST API for remote I/O operations
# It uses Flask to handle incoming requests and route them to the appropriate I/O functions
# It should be able to help the migrate command of IoP Cli to work remotely:
# this means copy all the .py files from the current directory of (settings.py) to the remote server
# and run the api migrate from the remote server
# the default folder is based on the NAMESPACE variable in settings.py
from flask import Flask, request, jsonify

@app.route('/remote_io', methods=['POST'])
def remote_io():
    data = request.json
    if not data or 'operation' not in data:
        return jsonify({'error': 'Invalid request'}), 400
    
    operation = data['operation']
    # Here you would implement the logic to handle the operation
    # For example, you could call a function that performs the I/O operation
    # and return the result as JSON.
    
    # Placeholder response for demonstration purposes
    response = {'status': 'success', 'operation': operation}
    return jsonify(response), 200

# ClassMethod UploadPackage(
# 	namespace As %String,
# 	body As %DynamicArray) As %DynamicObject
# {
#     // check for namespace existence and user permissions against namespace
# 	If '..NamespaceCheck(namespace) {
# 		Return ""
# 	}
# 	New $NAMESPACE
# 	Set $NAMESPACE = namespace
	
# 	//Create directory for custom packages
# 	Do ##class(%ZHSLIB.HealthShareMgr).GetDBNSInfo(namespace,.out)
# 	Set customPackagesPath = ##class(%Library.File).NormalizeDirectory("fhir_packages", out.globalsDatabase.directory)
# 	If '##class(%Library.File).DirectoryExists(customPackagesPath) {
# 		If '##class(%Library.File).CreateDirectory(customPackagesPath) {
# 			$$$ThrowStatus($$$ERROR($$$DirectoryCannotCreate, customPackagesPath))
# 		}
# 	}
	
# 	//Find package name
# 	Set iterator =  body.%GetIterator()
# 	Set packageName = ""
# 	While iterator.%GetNext(, .fileObject ) {
# 		If fileObject.name = "package.json" {
# 			Set packageName = fileObject.data.name_"@"_fileObject.data.version
# 		}	
# 	}
# 	If packageName = "" {
# 		Do ..%ReportRESTError($$$HTTP400,$$$ERROR($$$HSFHIRErrPackageNotFound))
# 		Return ""
# 	}
	
# 	Set packagePath = ##class(%Library.File).NormalizeDirectory(packageName, customPackagesPath)
# 	// If the package already exists then we must be meaning to re-load it. Delete files/directory/metadata and recreate fresh.
# 	If ##class(%Library.File).DirectoryExists(packagePath) {
# 		If '##class(%Library.File).RemoveDirectoryTree(packagePath) {
# 			$$$ThrowStatus($$$ERROR($$$DirectoryPermission , packagePath))
# 		}
# 	}
# 	If '##class(%Library.File).CreateDirectory(packagePath) {
# 		$$$ThrowStatus($$$ERROR($$$DirectoryCannotCreate, customPackagesPath))
# 	}
# 	Set pkg = ##class(HS.FHIRMeta.Storage.Package).FindById(packageName)
# 	If $ISOBJECT(pkg) {
# 		// Will fail and throw if the package is in-use or has dependencies preventing it from being deleted.
# 		Do ##class(HS.FHIRServer.ServiceAdmin).DeleteMetadataPackage(packageName)
# 	}
# 	Kill pkg

# 	//Unpack JSON objects		
# 	Set iterator = body.%GetIterator()
# 	While iterator.%GetNext(.key , .fileObject ) {
# 		Set fileName = ##class(%Library.File).NormalizeFilename(fileObject.name,packagePath)
# 		Set fileStream = ##class(%Stream.FileCharacter).%New()
# 		Set fileStream.TranslateTable = "UTF8"
# 		$$$ThrowOnError(fileStream.LinkToFile(fileName))
# 		Do fileObject.data.%ToJSON(.fileStream)
# 		$$$ThrowOnError(fileStream.%Save())
# 	}
	
# 	//Import package
# 	Do ##class(HS.FHIRMeta.Load.NpmLoader).importPackages(packagePath)
# 	Set pkg = ..GetOnePackage(packageName, namespace)
# 	Do ..%SetStatusCode($$$HTTP201)
# 	Do ..%SetHeader("location", %request.Application _ "packages/" _ packageName _ "?namespace=" _ namespace)
# 	Return pkg
# }