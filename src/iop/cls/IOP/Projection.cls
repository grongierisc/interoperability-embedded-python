Class IOP.Projection Extends %Projection.AbstractProjection
{

/// Projection to make install on compile
Projection Reference As Projection;

/// Call of the projection
ClassMethod CreateProjection(
	cls As %String,
	ByRef params) As %Status
{
    set tSC = $$$OK
    set tCurrentNamespace = $Namespace

    Try {
        set $NAMESPACE = "%SYS"
        // Create a new Web App for IOP Remote Handler
        set webName = "/api/iop" 
        set webProperties("NameSpace") = tCurrentNamespace 
        set webProperties("Enabled") = 1 
        set webProperties("DispatchClass") = "IOP.Service.Remote.Handler"
        set webProperties("AutheEnabled") = 32 
        set webProperties("ServeFiles")=2
        set webProperties("Recurse")=1
        if ##class(Security.Applications).Exists(webName) {
            // If the web application already exists, delete it first
            $$$ThrowOnError(##class(Security.Applications).Delete(webName))
        }
        $$$ThrowOnError(##class(Security.Applications).Create(webName, .webProperties))
    }
    Catch ex {

        Write !,"Error creating web application: ", ex.DisplayString(), !

    }

    znspace tCurrentNamespace
    Return tSC
}

ClassMethod RemoveProjection(
	cls As %String,
	ByRef params,
	recompile As %Boolean) As %Status
{
    Quit $$$OK
}

}
