from grongier.pex import BusinessProcess

from message import PostMessage
from obj import PostClass

import iris

class FilterPostRoutingRule(BusinessProcess):
    """
    This process receive a PostMessage containing a reddit post.
    It then understand if the post is about a dog or a cat or nothing and
    fill the right infomation inside the PostMessage before sending it to
    the FileOperation operation.
    """
    def on_init(self):
        
        if not hasattr(self,'target'):
            self.target = "Python.FileOperation"
        
        return

    def iris_to_python(self, request:'iris.dc.Demo.PostMessage'):

        request = PostMessage(post=PostClass(title=request.Post.Title, 
                                             selftext=request.Post.Selftext,
                                             author=request.Post.Author, 
                                             url=request.Post.Url,
                                             created_utc=request.Post.CreatedUTC,
                                             original_json=request.Post.OriginalJSON))
        return self.on_python_message(request)

    def on_python_message(self, request: PostMessage):
        if 'dog'.upper() in request.post.selftext.upper():
            request.to_email_address = 'dog@company.com'
            request.found = 'Dog'
        if 'cat'.upper() in request.post.selftext.upper():
            request.to_email_address = 'cat@company.com'
            request.found = 'Cat'

        if request.found is not None:
            self.send_request_sync(self.target,request)
        return
