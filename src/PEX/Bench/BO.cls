Class PEX.Bench.BO Extends Ens.BusinessOperation
{

Parameter INVOCATION = "Queue";

Method SampleCall(msg As Ens.Request, Output pResponse As Ens.Response) As %Status
{
    set dump = msg.PropertyName0
    set dump = msg.PropertyName1
    set dump = msg.PropertyName2
    set dump = msg.PropertyName1
    set dump = msg.PropertyName3
    set dump = msg.PropertyName4
    set dump = msg.PropertyName5
    set dump = msg.PropertyName6
    set dump = msg.PropertyName7
    set dump = msg.PropertyName8
    set dump = msg.PropertyName9
    Return ##class(Ens.Response).%New()
}

XData MessageMap
{
<MapItems>
    <MapItem MessageType="Ens.Request">
        <Method>SampleCall</Method>
    </MapItem>
</MapItems>
}

}
