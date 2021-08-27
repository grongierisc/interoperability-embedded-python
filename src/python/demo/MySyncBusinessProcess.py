import iris.pex
import demo.MyRequest

class MySyncBusinessProcess(iris.pex.BusinessProcess):

    PERSISTENT_PROPERTY_LIST="responses"
    
    def OnInit(self):
        print("[Python] ...MyBusinessProcess:OnInit() is called")
        self.responses = False
        return

    def OnTearDown(self):
        print("[Python] ...MyBusinessProcess:OnTeardown() is called")
        return

    def OnRequest(self, request):
        # called from ticker service, message is of type MyRequest with property requestString
        print("[Python] ...MyBusinessProcess:OnRequest() is called wth request: " + request.requestString)
        tRequest = demo.MyRequest.MyRequest()
        response = self.SendRequestSync("Demo.PEX.RandomGenerator", tRequest, timeout=7)
        if (response == None):
            print("sync call failed to return within time limit")
        else:
            self.responses=True
            print("returned from sync call with response: %d" % response.responseString)
        return

    def OnComplete(self, request, response):
        if (self.responses):
            print("[Python] ...MyBusinessProcess:OnComplete() is called after successful response")
        else:
            print("[Python] ...MyBusinessProcess:OnComplete() is called after unsuccesful response")
        return