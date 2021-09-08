Class PEX.MyBusinessOperationWithPythonAdapter Extends Ens.BusinessOperation
{

Parameter ADAPTER = "PEX.MyOutboundAdapter";

Property Adapter As PEX.MyOutboundAdapter;

Parameter INVOCATION = "Queue";

Method Method(pRequest As Ens.StringRequest, Output pResponse As Ens.Response) As %Status
{
    set tStatus = $$$OK
    set pResponse = ##class(Ens.StringResponse).%New()

    try{
        
        set str = ..Adapter.printString(pRequest.StringValue)
        set pResponse.StringValue = str
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
</MapItems>
}

}
