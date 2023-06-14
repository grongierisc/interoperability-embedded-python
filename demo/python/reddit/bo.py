
from grongier.pex import BusinessOperation, Utils

import iris

import os
import datetime
import smtplib
from email.mime.text import MIMEText

class EmailOperation(BusinessOperation):
    """
    This operation receive a PostMessage and send an email with all the
    important information to the concerned company ( dog or cat company )
    """
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
    """
    This operation receive a PostMessage and send an email with all the
    important information to the concerned company ( dog or cat company ) using the
    iris adapter EnsLib.EMail.OutboundAdapter
    """
    def get_adapter_type():
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
    """
    This operation receive a PostMessage and write down in the right company
    .txt all the important information and the time of the operation
    """
    def on_init(self):
        if hasattr(self,'path'):
            os.chdir(self.path)

    def say_hello(self, request:'iris.Ens.StringRequest'):
        self.log_info("Hello "+request.StringValue)

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
    """
    This operation receive a PostMessage and write down in the right company
    .txt all the important information and the time of the operation using the iris
    adapter EnsLib.File.OutboundAdapter
    """
    def get_adapter_type():
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
        
        self.Adapter.PutLine(filename, line)
        self.Adapter.PutLine(filename, "")
        self.Adapter.PutLine(filename, text)
        self.Adapter.PutLine(filename, " * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *")

        return

class HeartBeatOperation(BusinessOperation):

    def get_adapter_type():
        return "Python.TestHeartBeat"

    def on_keepalive(self):
        self.log_info('boop')

    def log(self,message):
        self.log_info(f'from log function : {message}')

    def on_message(self, request):
        self.adapter.on_task()
        return 

# Utils.register_component('adapter','TestHeartBeat','/irisdev/app/src/python/demo/',1,'Python.TestHeartBeat')
# Utils.register_component('bo','HeartBeatOperation','/irisdev/app/src/python/demo/reddit/',1,'Python.HeartBeatOperation')

if __name__ == '__main__':
    bo = FileOperation()

    bo.say_hello(iris.cls("Ens.StringRequest")._New("World"))