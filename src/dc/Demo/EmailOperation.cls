Class dc.Demo.EmailOperation Extends Ens.BusinessOperation
{

Property Adapter As EnsLib.EMail.OutboundAdapter;

Parameter ADAPTER = "EnsLib.EMail.OutboundAdapter";

Parameter INVOCATION = "Queue";

Method SendEmail(pRequest As dc.Demo.PostMessage, Output pResponse As Ens.Response) As %Status
{
    #dim mailMessage as %Net.MailMessage
    Set mailMessage = ##class(%Net.MailMessage).%New()
    Set mailMessage.Subject = pRequest.Found_" found"
    Do ..Adapter.AddRecipients(mailMessage,pRequest.ToEmailAddress)
    Set mailMessage.Charset="UTF-8"

    Set (title,author,url) = ""
    If ($IsObject(pRequest.Post)) {
        Set title = pRequest.Post.title
        Set author = pRequest.Post.author
        Set url = pRequest.Post.url
    }
    Do mailMessage.TextData.WriteLine("More info:")
    Do mailMessage.TextData.WriteLine("Title: "_title)
    Do mailMessage.TextData.WriteLine("Author: "_author)
    Do mailMessage.TextData.WriteLine("URL: "_url)
    Return ..Adapter.SendMail(mailMessage)
}

XData MessageMap
{
<MapItems>
    <MapItem MessageType="dc.Demo.PostMessage">
        <Method>SendEmail</Method>
    </MapItem>
</MapItems>
}

}
