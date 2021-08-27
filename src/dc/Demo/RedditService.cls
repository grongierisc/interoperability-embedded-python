Class dc.Demo.RedditService Extends Ens.BusinessService
{

Property Adapter As dc.Reddit.InboundAdapter;

Parameter ADAPTER = "dc.Reddit.InboundAdapter";

Method OnProcessInput(pInput As dc.Reddit.Post, pOutput As %RegisteredObject) As %Status
{
    Set msg = ##class(dc.Demo.PostMessage).%New()
    Set msg.Post = pInput
    Return ..SendRequestAsync("FilterPosts",msg)
}

}
