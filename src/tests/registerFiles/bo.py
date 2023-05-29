

from grongier.pex import BusinessOperation

import iris

from message import MyResponse

import os
import datetime
import smtplib
from email.mime.text import MIMEText

class EmailOperation(BusinessOperation):

    def OnMessage(self, pRequest):

        sender = 'admin@example.com'
        receivers = [ pRequest.ToEmailAddress ]


        port = 1025
        msg = MIMEText('This is test mail')

        msg['Subject'] = pRequest.Found+" found"
        msg['From'] = 'admin@example.com'
        msg['To'] = pRequest.ToEmailAddress

        with smtplib.SMTP('localhost', port) as server:
            
            # server.login('username', 'password')
            server.sendmail(sender, receivers, msg.as_string())
            print("Successfully sent email")



class EmailOperationWithIrisAdapter(BusinessOperation):

    def get_adapter_type():
        """
        Name of the registred Adapter
        """
        return "EnsLib.EMail.OutboundAdapter"

    def OnMessage(self, pRequest):

        mailMessage = iris.cls("%Net.MailMessage")._New()
        mailMessage.Subject = pRequest.Found+" found"
        self.Adapter.AddRecipients(mailMessage,pRequest.ToEmailAddress)
        mailMessage.Charset="UTF-8"

        title = author = url = ""
        if (pRequest.Post is not None) :
            title = pRequest.Post.title
            author = pRequest.Post.author
            url = pRequest.Post.url
        
        mailMessage.TextData.WriteLine("More info:")
        mailMessage.TextData.WriteLine("Title: "+title)
        mailMessage.TextData.WriteLine("Author: "+author)
        mailMessage.TextData.WriteLine("URL: "+url)

        return self.Adapter.SendMail(mailMessage)

class FileOperation(BusinessOperation):

    def OnInit(self):
        if hasattr(self,'Path'):
            os.chdir(self.Path)

    def OnMessage(self, pRequest):
        
        ts = title = author = url = text = ""

        if (pRequest.Post is not None):
            title = pRequest.Post.Title
            author = pRequest.Post.Author
            url = pRequest.Post.Url
            text = pRequest.Post.Selftext
            ts = datetime.datetime.fromtimestamp(pRequest.Post.CreatedUTC).__str__()

        line = ts+" : "+title+" : "+author+" : "+url
        filename = pRequest.Found+".txt"


        self.PutLine(filename, line)
        self.PutLine(filename, "")
        self.PutLine(filename, text)
        self.PutLine(filename, " * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *")

        return 

    def PutLine(self,filename,string):
        try:
            with open(filename, "a",encoding="utf-8") as outfile:
                outfile.write(string)
        except Exception as e:
            raise e

class FileOperationWithIrisAdapter(BusinessOperation):

    def get_adapter_type():
        """
        Name of the registred Adapter
        """
        return "EnsLib.File.OutboundAdapter"

    def OnMessage(self, pRequest):

        ts = title = author = url = text = ""

        if (pRequest.Post != ""):
            title = pRequest.Post.Title
            author = pRequest.Post.Author
            url = pRequest.Post.Url
            text = pRequest.Post.Selftext
            ts = iris.cls("%Library.PosixTime").LogicalToOdbc(iris.cls("%Library.PosixTime").UnixTimeToLogical(pRequest.Post.CreatedUTC))

        line = ts+" : "+title+" : "+author+" : "+url
        filename = pRequest.Found+".txt" 
        
        self.Adapter.PutLine(filename, line)
        self.Adapter.PutLine(filename, "")
        self.Adapter.PutLine(filename, text)
        self.Adapter.PutLine(filename, " * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *")

        return

class MyOperation(BusinessOperation):

    def OnMessage(self, request):
        self.LOGINFO('hello')
        return MyResponse(request.StringValue)

if __name__ == "__main__":
    
    op = FileOperation()
    from message import PostMessage,PostClass
    msg = PostMessage(PostClass('foo','foo','foo','foo',1,'foo'),'bar','bar')
    op.OnMessage(msg)