Class dc.Demo.FileOperation Extends Ens.BusinessOperation
{

Property Adapter As EnsLib.File.OutboundAdapter;

Parameter ADAPTER = "EnsLib.File.OutboundAdapter";

Parameter INVOCATION = "Queue";

Method WriteToFile(pRequest As dc.Demo.PostMessage, Output pResponse As Ens.Response) As %Status
{
    Set (ts, title, author, url, text) = ""
    If ($IsObject(pRequest.Post)) {
        Set title = pRequest.Post.Title
        Set author = pRequest.Post.Author
        Set url = pRequest.Post.Url
        Set text = pRequest.Post.Selftext
        Set ts = ##class(%Library.PosixTime).LogicalToOdbc(##class(%Library.PosixTime).UnixTimeToLogical(pRequest.Post.CreatedUTC))
    }
    Set line = ts_" : "_title_" : "_author_" : "_url
    Set filename = pRequest.Found_".txt" 
    $$$QuitOnError(..Adapter.PutLine(filename, line))
    $$$QuitOnError(..Adapter.PutLine(filename, ""))
    $$$QuitOnError(..Adapter.PutLine(filename, text))
    $$$QuitOnError(..Adapter.PutLine(filename, " * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *"))
    Return $$$OK
}

XData MessageMap
{
<MapItems>
    <MapItem MessageType="dc.Demo.PostMessage">
        <Method>WriteToFile</Method>
    </MapItem>
</MapItems>
}

}
