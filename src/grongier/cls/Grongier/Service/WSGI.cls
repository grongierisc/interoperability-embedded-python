Class Grongier.Service.WSGI Extends (%RegisteredObject, %CSP.REST) [ ServerOnly = 1 ]
{

Parameter CLASSPATHS;

Parameter MODULENAME;

Parameter APPNAME;

/// Helper method to write data to the output stream
ClassMethod write(data)
{
    w data
}

/// Helper to build the environ
ClassMethod GetEnviron() As %SYS.Python
{
    //set builtins
    set builtins = ##class(%SYS.Python).Import("builtins")

    //import dict to create environ
    set dict = builtins.dict()

    #dim %request As %CSP.Request

    //set environ 
    do dict."__setitem__"("SERVER_NAME", $System.INetInfo.LocalHostName())
    do dict."__setitem__"("SERVER_PORT", "")
    do dict."__setitem__"("SERVER_PROTOCOL", "HTTP/1.1")
    do dict."__setitem__"("SERVER_SOFTWARE", "IRIS")
    do dict."__setitem__"("SCRIPT_NAME", ..#APPNAME)
    do dict."__setitem__"("REQUEST_METHOD", %request.Method)
    do dict."__setitem__"("CONTENT_TYPE", %request.ContentType)
    do dict."__setitem__"("CHARSET", %request.CharSet)
    Set app=$$getapp^%SYS.cspServer(%request.URL,.path,.match,.updatedurl)
    do dict."__setitem__"("PATH_INFO", $extract(updatedurl,$length(path),*))

    // to extract the query string

    return dict
}

/// Implement a singleton pattern to get the python app
ClassMethod GetPyhonApp() As %SYS.Python
{
    if ..#CLASSPATHS '="" {
        set sys = ##class(%SYS.Python).Import("sys")
        set delimiter = $s($system.Version.GetOS()="Windows":";",1:":")
        set extraClasspaths = $tr(..#CLASSPATHS,delimiter,"|")
        for i=1:1:$l(extraClasspaths,"|") {
            set onePath = $p(extraClasspaths,"|",i)
            set onePath = ##class(%File).NormalizeDirectory(onePath)
            if onePath?1"$$IRISHOME"1P.E set onePath = $e($system.Util.InstallDirectory(),1,*-1)_$e(onePath,11,*)
            if onePath'="" do sys.path.append(onePath)
        }
    }

    //import module
    set module = ##class(%SYS.Python).Import(..#MODULENAME)

    //set builtins
    set builtins = ##class(%SYS.Python).Import("builtins")

    //set app
    set application = builtins.getattr(module, ..#APPNAME)

    Return application
}

ClassMethod Page(skipheader As %Boolean = 1) As %Status [ Internal, ServerOnly = 1 ]
{
    Try {
        
        //set environ
        set environ = ..GetEnviron()

        //import sys
        set sys = ##class(%SYS.Python).Import("sys")

        //set stdin
        set builtins = ##class(%SYS.Python).Import("builtins")
        set ba = builtins.bytearray()
        
        while %request.Content.AtEnd = 0 {
            do ba.extend(##class(%SYS.Python).Bytes(%request.Content.Read()))
        }
        //set handler
        set handler = ##class(%SYS.Python).Import("grongier.pex.wsgi.handlers").IrisHandler(ba, sys.stdout, sys.stderr,environ)

        // get a singleton app
        set application = ..GetPyhonApp()

        //run app
        do handler.run(application)

    }
    Catch ex {
        return ex.AsStatus()
    }

    quit $$$OK
}

}
