Class IOP.Wrapper Extends %RegisteredObject
{

ClassMethod Import(
	moduleName As %String,
	path As %String = "",
	debugPort As %Integer = 0) As %Status
{
    set tSC = $$$OK
    Try {
        do ##class(IOP.Common).SetPythonPath(path)
        // For traceback debugging
        do $system.Python.Debugging(1)
        if debugPort > 0 {
            
            set debugpy = ##class(%SYS.Python).Import("iop._debugpy")
            do debugpy."debugpy_in_iris"($zu(12),debugPort)
        }

        // Import the module
        set tModule = ##class(%SYS.Python).Import(moduleName)

    }
    Catch ex {
        Set tSC= ##class(IOP.Wrapper).DisplayTraceback(ex)
        throw ex
    }
    return tModule
}

ClassMethod DisplayTraceback(ex) As %Status
{
    set tSC = ex.AsStatus()

    // Import Modules
    set sys = ##class(%SYS.Python).Import("sys")
    set tracebackModule = ##class(%SYS.Python).Import("traceback")
    set builtins = ##class(%SYS.Python).Import("builtins")
    // Get the last traceback
    set traceback = sys."last_traceback"
    set exType = sys."last_type"."__name__"
    set exValue = sys."last_value"."__str__"()
    // Check if traceback is an object
    if $isObject(traceback) {
        // Format the traceback
        set tb = tracebackModule."format_exception"(sys."last_type", sys."last_value", traceback)
        set tbString = ""
        for i=0:1:(tb."__len__"()-1) {
            set tbString = tbString _ $c(10)_$c(13) _ tb."__getitem__"(i)
        }
        w tbString
        set tSC = $$$ERROR("Exception in Python - "_exType_" - "_exValue)
    }
    
    return tSC
}

}
