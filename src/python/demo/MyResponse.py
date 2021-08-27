import pex

class MyResponse(pex.Message):

    def __init__(self, res=None):
        super().__init__()
        self.responseString = res