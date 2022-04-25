from grongier.pex import BusinessProcess

from message import PostMessage

class FilterPostRoutingRule(BusinessProcess):
    
    def OnInit(self):
        
        if not hasattr(self,'Target'):
            self.Target = "Python.FileOperation"
        
        return

    def OnRequest(self, request: PostMessage):
        if 'dog'.upper() in request.Post.Selftext.upper():
            request.ToEmailAddress = 'dog@company.com'
            request.Found = 'Dog'
        if 'cat'.upper() in request.Post.Selftext.upper():
            request.ToEmailAddress = 'cat@company.com'
            request.Found = 'Cat'
        return self.SendRequestSync(self.Target,request)
