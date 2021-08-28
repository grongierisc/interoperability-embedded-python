/// Description
Class Grongier.PEX.Test
{

/// Register
ClassMethod Register() As %Status
{
	Set sc = $$$OK
	zw ##class(Grongier.PEX.Utils).RegisterComponent("MyCombinedBusinessOperation","MyCombinedBusinessOperation","/irisdev/app/src/python/demo/",1,"PEX.MyCombinedBusinessOperation")
	Return sc
}

ClassMethod TestBO() As %Status
{
	try {
	Set sc = $$$OK
	set mybo = ##class(Grongier.PEX.BusinessOperation).%New("mybo")
	set mybo.%classpaths = "/irisdev/app/src/python:/irisdev/app/src/python/demo"
	set mybo.%module = "MyBusinessOperation"
	set mybo.%classname = "MyBusinessOperation"
	$$$ThrowOnError(mybo.OnInit())
	set request = ##class(Ens.StringRequest).%New("hello")
	set request = ##class(EnsLib.PEX.Message).%New()
	set request.%classname = "MyRequest.MyRequest"
	set dyna = {"requestString":"hello!"}
	set request.%jsonObject = dyna
	Try {
		$$$ThrowOnError(mybo.OnMessage(request,.response))
		zw response
	} catch importEx {
		WRITE $System.Status.GetOneStatusText(importEx.AsStatus(),1),!
	}
	} catch ex {
		WRITE $System.Status.GetOneStatusText(ex.AsStatus(),1),!
	}

	Return sc
}

/// List
ClassMethod PythonList() [ Language = python ]
{
return [ 1, 3 ]
}

}
