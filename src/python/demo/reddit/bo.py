

from grongier.pex import BusinessOperation

from message import MyRequest,MyMessage

import iris

import os
import datetime
import smtplib
from email.mime.text import MIMEText

class EmailOperation(BusinessOperation):

    def on_message(self, request):

        sender = 'admin@example.com'
        receivers = [ request.to_email_address ]


        port = 1025
        msg = MIMEText('This is test mail')

        msg['Subject'] = request.found+" found"
        msg['From'] = 'admin@example.com'
        msg['To'] = request.to_email_address

        with smtplib.SMTP('localhost', port) as server:
            
            # server.login('username', 'password')
            server.sendmail(sender, receivers, msg.as_string())
            print("Successfully sent email")



class EmailOperationWithIrisAdapter(BusinessOperation):

    def getAdapterType():
        """
        Name of the registred Adapter
        """
        return "EnsLib.EMail.OutboundAdapter"

    def on_message(self, request):

        mail_message = iris.cls("%Net.mail_message")._New()
        mail_message.Subject = request.found+" found"
        self.Adapter.AddRecipients(mail_message,request.to_email_address)
        mail_message.Charset="UTF-8"

        title = author = url = ""
        if (request.post is not None) :
            title = request.post.title
            author = request.post.author
            url = request.post.url
        
        mail_message.TextData.WriteLine("More info:")
        mail_message.TextData.WriteLine("title: "+title)
        mail_message.TextData.WriteLine("author: "+author)
        mail_message.TextData.WriteLine("URL: "+url)

        return self.Adapter.SendMail(mail_message)

class FileOperation(BusinessOperation):

    def on_init(self):
        if hasattr(self,'path'):
            os.chdir(self.path)

    def on_message(self, request):
        
        ts = title = author = url = text = ""

        if (request.post is not None):
            title = request.post.title
            author = request.post.author
            url = request.post.url
            text = request.post.selftext
            ts = datetime.datetime.fromtimestamp(request.post.created_utc).__str__()

        line = ts+" : "+title+" : "+author+" : "+url
        filename = request.found+".txt"


        self.put_line(filename, line)
        self.put_line(filename, "")
        self.put_line(filename, text)
        self.put_line(filename, " * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *")

        return 

    def put_line(self,filename,string):
        try:
            with open(filename, "a",encoding="utf-8") as outfile:
                outfile.write(string)
        except Exception as e:
            raise e

class FileOperationWithIrisAdapter(BusinessOperation):

    def getAdapterType():
        """
        Name of the registred Adapter
        """
        return "EnsLib.File.OutboundAdapter"

    def on_message(self, request):

        ts = title = author = url = text = ""

        if (request.post != ""):
            title = request.post.title
            author = request.post.author
            url = request.post.url
            text = request.post.selftext
            ts = iris.cls("%Library.PosixTime").LogicalToOdbc(iris.cls("%Library.PosixTime").UnixTimeToLogical(request.post.created_utc))

        line = ts+" : "+title+" : "+author+" : "+url
        filename = request.found+".txt" 
        
        self.Adapter.put_line(filename, line)
        self.Adapter.put_line(filename, "")
        self.Adapter.put_line(filename, text)
        self.Adapter.put_line(filename, " * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *")

        return

class MyOperation(BusinessOperation):

    def on_message(self, request):
        self.log_info('hello')
        return

    def my_request(self,request:MyRequest):
        return iris.cls('Ens.StringResponse')._New(request.ma_string)

    def my_iris(self,request:'iris.Ens.Request'):
        self.log_info(self.maVar)
        return MyMessage('toto')


if __name__ == "__main__":
    crud_person = EmailOperationWithIrisAdapter()
    crud_person._dispatchon_init('')
    request = iris.cls('Ens.StringRequest')._New('toto')
    response = crud_person._dispatchon_messag(request)
