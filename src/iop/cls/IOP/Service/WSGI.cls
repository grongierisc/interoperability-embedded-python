Class IOP.Service.WSGI Extends %CSP.REST [ ServerOnly = 1 ]
{

Parameter CLASSPATHS;

Parameter MODULENAME;

Parameter APPNAME;

Parameter DEVMODE = 1;

/// This method matches the request and method and calls the dispatcher
ClassMethod Page(skipheader As %Boolean = 0) As %Status [ ProcedureBlock = 1 ]
{
    #dim tSC As %Status = $$$OK
    #dim e As %Exception.AbstractException
    
    #dim tAuthorized,tRedirected As %Boolean
    #dim tRedirectRoutine,tURL As %String = ""
    #dim %response As %CSP.Response
        
    Try {

        #; Ensure that we honor the requested charset 
        Set %response.CharSet=..#CHARSET

        #; Ensure that we honor the requested CONTENTTYPE
        If ..#CONTENTTYPE'="" Set %response.ContentType=..#CONTENTTYPE 

        #; Ensure that we honor the requested HTTP_ACCEPT_LANGUAGE 
        Set %response.Domain = ..#DOMAIN
        Do %response.MatchLanguage() 
        


        #; Record if device re-direction is already active
        Set tRedirected=##class(%Library.Device).ReDirectIO()
        
        #; Record the redirect routine
        Set tRedirectRoutine=$System.Device.GetMnemonicRoutine()

        #; Now switch to using THIS routine for device redirection
        Use $io::("^%SYS.cspServer2")

        #; Switch device redirection on (may already be on but thats ok)
        Do ##class(%Library.Device).ReDirectIO(1)

        #; Ensure that the application is defined (security check)
        If $$$GetSecurityApplicationsDispatchClass(%request.AppData)="" {
             
             #; Report not authorized
             Set tSC=..Http403()
             
             #; Done
             Quit
        }
        
        #; GgiEnvs are not defined in the CSP shell
        Set tURL=$Get(%request.CgiEnvs("CSPLIB"))
        If tURL="" Set tURL=%request.URL
          
        #; Do an access check
        Set tSC=..AccessCheck(.tAuthorized)
        If $$$ISERR(tSC) Quit

        If tAuthorized=0 {
            
            #; Don't want the session token
            Set %response.OutputSessionToken=0
            
            #; Set the Http Status
            Set %response.Status=..#HTTP403FORBIDDEN
            
            #; Done
            Quit
        }
        
        #; Extract the match url from the application name
        Set tMatchUrl = "/"_$Extract(tURL,$Length(%request.Application)+1,*)

        #; Dispatch the request
        Set tSC=..DispatchRequest(tMatchUrl,%request.Method)
        
    } Catch (e) {
        Set tSC=e.AsStatus()
    }
    
    If $$$ISERR(tSC) {
        
        #; Don't want the session token
        Set %response.OutputSessionToken=0
        
        Do ..Http500(##class(%Exception.StatusException).CreateFromStatus(tSC))
    }

    #; Ensure that at least something is written out as the body
    #; This will trigger the device redirect capture and force headers to be written
    #; (if not already done)
    Write ""
    
    #; Reset redirect device if necessary
    If tRedirected {
        
        #; Use the original redirected routine
        Use $io::("^"_tRedirectRoutine)
        
        #; Switch device redirection on
        Do ##class(%Library.Device).ReDirectIO(1)
    }

    if ..#DEVMODE {
        #; Close the device to ensure next request starts with a new process
        Close 0
    }

    Quit $$$OK
}

ClassMethod OnPreDispatch(
	pUrl As %String,
	pMethod As %String,
	ByRef pContinue As %Boolean) As %Status
{
         Set path = ..#CLASSPATHS
         Set appName = ..#APPNAME
         Set module = ..#MODULENAME
         Set devmode = ..#DEVMODE
         Set pContinue = 1
         Do ..DispatchREST(pUrl, path, appName, module, devmode)
         Quit $$$OK
}

ClassMethod DispatchREST(
	PathInfo As %String,
	appPath As %String,
	appName As %String,
	module As %String,
	devmode As %Boolean = 1) As %Status
{
           Set builtins = ##CLASS(%SYS.Python).Builtins()
           Set interface = ##CLASS(%SYS.Python).Import("grongier.pex.wsgi.handlers")
           Set rawformdata = ""
           Set environ = builtins.dict()
           Set key = %request.NextCgiEnv("")

           // Let's check if the WSGI application has been loaded or not for this session.
           
           If (($DATA(%session.Data("application")) && $ISOBJECT(%session.Data("application"))) && 'devmode) {
            Set application = %session.Data("Application")
           }
           Else{

            Set application = ..GetPythonClass(appName, module, appPath)
            If application = "" {
                throw ##class(%Exception.General).%New("Error loading WSGI application: "_module_"."_appName_" from "_appPath)
            }
            Else {
               Set %session.Data("Application") = application
            }
           }

           // Editing some CGI variables that may be incorrect in %request
           // Also filling in environ with as many CGI variables as possible from %request
           // WSGI states that all CGI variables are valid and should be included if possible
           While (key'="") {
              Set value = %request.GetCgiEnv(key)
              If key = "PATH_INFO" {
               Set app=$$getapp^%SYS.cspServer(%request.URL,.path,.match,.updatedurl)
               Set value = $EXTRACT(updatedurl,$LENGTH(path),*)
              }
              If key = "SCRIPT_NAME" {
               //%request will sometimes have Script_name include Path_info
               Set value = $PIECE(%request.Application, "/",1,*-1)
              }
              Do environ."__setitem__"(key,value)
              Set key = %request.NextCgiEnv(key)
           }

           //Have to set up a correct wsgi.input stream from %request
           Set stream = %request.Content
           
           Set contentType = %request.ContentType
           Set contentLength = 0

           If contentType = "application/x-www-form-urlencoded" {
            Set formdict = builtins.dict()
            Set key = $ORDER(%request.Data(""))
            While (key'="") {
               Set value = $GET(%request.Data(key,1))
               Do formdict."__setitem__"(key,value)
               Set key = $ORDER(%request.Data(key))
            }
            Do environ."__setitem__"("formdata", formdict)
           }
           ElseIf contentType = "multipart/form-data" {
            Set boundary = $PIECE(%request.GetCgiEnv("CONTENT_TYPE"), "=",2)
            Set stream = ##CLASS(%CSP.BinaryStream).%New()

            Do stream.Write($CHAR(13,10))

            //Get the Form Data values

            Set key = $ORDER(%request.Data(""))
            While (key'="") {
               Do stream.Write("--")
               Do stream.Write(boundary)
               Do stream.Write($CHAR(13,10))
               Set value = $GET(%request.Data(key,1))
               Do stream.Write("Content-Disposition: form-data; name=")
               Do stream.Write(""""_key_"""")
               Do stream.Write($CHAR(13,10,13,10))
               Do stream.Write(value)
               Do stream.Write($CHAR(13,10))
               Set key = $ORDER(%request.Data(key))
            }

            //Now get the possible MIME data streams
            Set key = %request.NextMimeData("")
            While key'="" {
               Set numMimeStreams = %request.CountMimeData(key)
               Set index = %request.NextMimeDataIndex(key, "")
               Do stream.Write("--")
               Do stream.Write(boundary)
               Do stream.Write($CHAR(13,10))
               If numMimeStreams > 1 {
                  //I need to create a boundary for a nested multipart content type
                  Set internalboundary = "--"
                  For i = 1 : 1 : 7 {
                     Set internalboundary = internalboundary _ $RANDOM(10)
                  }
                  While index '= "" {
                     Set mimestream = %request.GetMimeData(key, index)
                     Set headers = mimestream.Headers
                     Do stream.Write("--")
                     Do stream.Write(internalboundary)
                     Do stream.Write($CHAR(13,10))
                     Do stream.Write(headers)
                     Do stream.Write($CHAR(13,10,13,10))
                     Set sc = stream.CopyFrom(mimestream)
                     //TODO error handling
                     Do stream.Write($CHAR(13,10))
                     Set index = %request.NextMimeDataIndex(key, index)
                  }
                  Do stream.Write("--")
                  Do stream.Write(internalboundary)
                  Do stream.Write("--")
               }
               Else {
                  Set mimestream = %request.GetMimeData(key, index)
                  Set headers = mimestream.Headers
                  Do stream.Write(headers)
                  Do stream.Write($CHAR(13,10,13,10))
                  Set sc = stream.CopyFrom(mimestream)
                  //TODO error handling
                  Do stream.Write($CHAR(13,10))
               }
               Set key = %request.NextMimeData(key)
            }
            Do stream.Write("--")
            Do stream.Write(boundary)
            Do stream.Write("--")
            Do stream.Rewind()
           }


           Try {
            Do interface."make_request"(environ, stream, application, appPath)
           }
           Catch exception {
            throw exception
           }
           Quit $$$OK
}

ClassMethod GetPythonClass(
	pClassname As %String,
	pModule As %String,
	pClasspath As %String) As %SYS.Python
{
	Try {
		If pClasspath '="" {
            set sys = ##class(%SYS.Python).Import("sys")

                for i=0:1:(sys.path."__len__"()-1) {
                    Try {
                        if sys.path."__getitem__"(i) = pClasspath {
                            do sys.path."__delitem__"(i)
                        }
                    }
                    Catch ex {
                        // do nothing
                    }

                }
                do sys.path.insert(0, pClasspath)
		}

		Set importlib = ##class(%SYS.Python).Import("importlib")
		Set builtins = ##class(%SYS.Python).Import("builtins")
		Set module = importlib."import_module"(pModule)
		Set class = builtins.getattr(module, pClassname)
   }
   Catch ex {
        throw ##class(%Exception.General).%New("Error loading WSGI application: "_pModule_"."_pClassname_" from "_pClasspath)
   }
	
	Quit class
}

}
