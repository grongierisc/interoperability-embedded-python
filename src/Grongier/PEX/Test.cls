/// Description
Class Grongier.PEX.Test
{

ClassMethod TestBO() As %Status
{
	Set sc = $$$OK
	set mybo = ##class(Grongier.PEX.BusinessOperation).%New("mybo")
	set mybo.%classpaths = "/irisdev/app/src/python/demo/:/usr/irissys/mgr/python/"
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

	Return sc
}

}
