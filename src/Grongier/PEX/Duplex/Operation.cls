Class Grongier.PEX.DuplexOperation Extends Grongier.PEX.PrivateSessionDuplex
{

ClassMethod OnBusinessType(pItem As Ens.Config.Item) As %Integer
{
    Quit $$$eHostTypeOperation
}

XData MessageMap
{
<MapItems>
<MapItem MessageType="Grongier.PEX.PrivateSession.Message.Start"><Method>OnMsgPrivateSessionStart</Method></MapItem>
<MapItem MessageType="Grongier.PEX.PrivateSession.Message.Stop"><Method>OnMsgPrivateSessionStop</Method></MapItem>
<MapItem MessageType="Grongier.PEX.PrivateSession.Message.Poll"><Method>OnMsgPrivateSessionPoll</Method></MapItem>
</MapItems>
}

}
