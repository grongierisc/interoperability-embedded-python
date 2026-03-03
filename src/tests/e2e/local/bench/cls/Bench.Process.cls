Class Bench.Process Extends Ens.BusinessProcess
{

Property TargetConfigName As %String(MAXLEN = 1000) [ InitialExpression = "Bench.Operation" ];

Property Size As %Integer [ InitialExpression = 100 ];

Parameter SETTINGS = "Size:Basic,TargetConfigName:Basic";

Method OnRequest(
	pDocIn As %Library.Persistent,
	Output pDocOut As %Library.Persistent) As %Status
{
    set status = $$$OK

    try {

        for i=1:1:..Size {
            $$$ThrowOnError(..SendRequestSync(..TargetConfigName,pDocIn,.pDocOut))
        }
        
    } catch ex {
        set status = ex.AsStatus()
    }

    Quit status
}

Storage Default
{
<Data name="ProcessDefaultData">
<Subscript>"Process"</Subscript>
<Value name="1">
<Value>TargetConfigNames</Value>
</Value>
<Value name="2">
<Value>Size</Value>
</Value>
<Value name="3">
<Value>TargetConfigName</Value>
</Value>
</Data>
<DefaultData>ProcessDefaultData</DefaultData>
<Type>%Storage.Persistent</Type>
}

}
