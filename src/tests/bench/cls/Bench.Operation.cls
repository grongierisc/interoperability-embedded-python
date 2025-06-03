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
        hang 0.01
        set pResponse = pRequest

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
        <Method>Method</Method>
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
