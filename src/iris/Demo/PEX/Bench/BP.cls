/// Description
Class PEX.Bench.BP Extends Ens.BusinessProcess [ ClassType = persistent, ProcedureBlock ]
{

Method OnRequest(pRequest As Ens.Request, Output pResponse As Ens.Response) As %Status
{
    set sc =$$$OK

    set start = $P($ZTS,",",2)

    For i = 1:1:1000 {
        set msg = ##class(PEX.Bench.MSG).%New()
        
        set msg.PropertyName0 = "PropertyName0"
        set msg.PropertyName1 = "PropertyName0"
        set msg.PropertyName2 = "PropertyName0"
        set msg.PropertyName3 = "PropertyName0"
        set msg.PropertyName4 = "PropertyName0"
        set msg.PropertyName5 = "PropertyName0"
        set msg.PropertyName6 = "PropertyName0"
        set msg.PropertyName7 = "PropertyName0"
        set msg.PropertyName8 = "PropertyName0"
        set msg.PropertyName9 = "PropertyName0"

        $$$ThrowOnError(..SendRequestSync("PEX.Bench.BO",msg))

        Write i, !
    }

    s end=$P($ZTS,",",2)

    $$$LOGINFO(end-start)

    set pResponse = ##class(Ens.StringResponse).%New(end-start)

    Return sc
}

Storage Default
{
<Type>%Storage.Persistent</Type>
}

}
