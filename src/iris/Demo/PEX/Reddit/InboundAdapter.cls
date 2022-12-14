Class dc.Reddit.InboundAdapter Extends Ens.InboundAdapter
{

Property LastPostName As %String;

Property SSLConfig As %String;

Parameter SERVER = "www.reddit.com";

Property Feed As %String;

/// how many messages to receive per request
Property Limit As %Integer;

Parameter SETTINGS = "SSLConfig:Connection:sslConfigSelector,Feed:Connection,Limit:Connection";

Method OnInit() As %Status
{
    If (..SSLConfig = "") {
        return $$$ERROR(5001, "SSLConfig required")
    }
    If (..Feed="") { 
        Set ..Feed = "/new/"
    }
    Set ..LastPostName = ""
    
    Quit $$$OK
}

Method OnTask() As %Status
{
    $$$TRACE("LIMIT:"_..Limit)
    If ((..SSLConfig="") || (..Feed="")) {
        Return $$$OK 
    }
    Set tSC = 1
    // HTTP Request
    #dim httprequest as %Net.HttpRequest
    #dim httpResponse as %Net.HttpResponse
    Try {
        Set httprequest = ##class(%Net.HttpRequest).%New()
        Do httprequest.ServerSet(..#SERVER)
        Do httprequest.SSLConfigurationSet(..SSLConfig)
        Set requestString = ..Feed_".json?before="_..LastPostName_"&limit="_..Limit
        $$$TRACE(requestString)
        Do httprequest.Get(requestString)
        Set httpResponse = httprequest.HttpResponse
        If (httpResponse.StatusCode '=200) {
            $$$ThrowStatus($$$ERROR(5001, "HTTP StatusCode = "_httpResponse.StatusCode))
        } 
        Set jo = {}.%FromJSON(httpResponse.Data)
        Set iter = jo.data.children.%GetIterator()
        Set updateLast = 0
        While iter.%GetNext(.key , .value ) {
            If (value.data.selftext="") { Continue }            
            Set post = ##class(dc.Reddit.Post).%New()
            $$$ThrowOnError(post.%JSONImport(value.data))
            Set post.OriginalJSON = value.%ToJSON()
            $$$ThrowOnError(post.%Save())
            If ('updateLast) {
                Set ..LastPostName = value.data.name
                Set updateLast = 1
            }
            $$$ThrowOnError(..BusinessHost.ProcessInput(post))
        }
    } Catch ex {
        Do ex.Log()
        Set tSC = ex.AsStatus()
    }
    Set ..BusinessHost.%WaitForNextCallInterval=1
    Quit tSC
}

}
