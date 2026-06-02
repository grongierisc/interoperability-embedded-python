from iop import BusinessProcess

from message import PostMessage

class FilterPostRoutingRule(BusinessProcess):
    
    def on_init(self):
        
        if not hasattr(self,'Target'):
            self.Target = "Python.FileOperation"
        
        return

    def on_request(self, request: PostMessage):
        if 'dog'.upper() in request.Post.Selftext.upper():
            request.ToEmailAddress = 'dog@company.com'
            request.Found = 'Dog'
        if 'cat'.upper() in request.Post.Selftext.upper():
            request.ToEmailAddress = 'cat@company.com'
            request.Found = 'Cat'
        return self.send_request_sync(self.Target,request)
