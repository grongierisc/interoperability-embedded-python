Class Bench.Operation Extends Ens.BusinessOperation
{

Parameter INVOCATION = "Queue";

Method Method(
	pRequest As Ens.Request,
	Output pResponse As Ens.Response) As %Status
{
    set tStatus = $$$OK
    set pResponse = ##class(Ens.Response).%New()

    try{
        // Simulate some processing time
        hang 0.001
        set pResponse = pRequest

    }
    catch exp
    {
        set tStatus = exp.AsStatus()
    }
    Quit tStatus
}

/// Description
Method MethodRandom(
	pRequest As Ens.StringRequest,
	Output pResponse As Ens.StringResponse) As %Status
{
    set tStatus = $$$OK
    set pResponse = ##class(Ens.StringResponse).%New()

    try{
        set pResponse.StringValue = $R(1000000) // Return a random number as string

    }
    catch exp
    {
        set tStatus = exp.AsStatus()
    }
    Quit tStatus
}

XData MessageMap
{
<MapItems>
    <MapItem MessageType="Ens.Request">
        <Method>MethodRandom</Method>
    </MapItem>
    <MapItem MessageType="IOP.Message">
        <Method>Method</Method>
    </MapItem>
    <MapItem MessageType="IOP.PickleMessage">
        <Method>Method</Method>
    </MapItem>
</MapItems>
}

}
