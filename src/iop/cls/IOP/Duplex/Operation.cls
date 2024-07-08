Class IOP.DuplexOperation Extends IOP.PrivateSessionDuplex
{

ClassMethod OnBusinessType(pItem As Ens.Config.Item) As %Integer
{
    Quit $$$eHostTypeOperation
}

XData MessageMap
{
<MapItems>
<MapItem MessageType="Ens.Request"><Method>OnMessage</Method></MapItem>
</MapItems>
}

Method OnMessage(
	request As %Library.Persistent,
	Output response As %Library.Persistent) As %Status
{
	set tSC = $$$OK
	try {
		set response = ..%class."_dispatch_on_message"(request)
	} catch ex {
		set tSC = ex.AsStatus()
	}
	quit tSC
}

}
