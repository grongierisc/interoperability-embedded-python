import iris.pex
import demo.MyRequest

class MyBusinessProcess(iris.pex.BusinessProcess):

    PERSISTENT_PROPERTY_LIST=["runningTotal", "responses"]
    
    def OnInit(self):
        print("[Python] ...MyBusinessProcess:OnInit() is called")
        self.runningTotal = 0
        self.responses = False
        return

    def OnTearDown(self):
        print("[Python] ...MyBusinessProcess:OnTeardown() is called")
        return

    def OnRequest(self, request):
        # called from ticker service, message is of type MyRequest with property requestString
        print("[Python] ...MyBusinessProcess:OnRequest() is called wth request: " + request.requestString)
        for i in range(4):
            key = "request # %d" % (i+1)
            tRequest = demo.MyRequest.MyRequest()
            self.SendRequestAsync("Demo.PEX.RandomGenerator", tRequest, True, key, None)
        self.SetTimer(7, "myTimer")
        return

    def OnResponse(self, request, response, callRequest, callResponse, pCompletionKey):
        if (pCompletionKey == "myTimer"):
            print("[Python] ...MyBusinessProcess:OnResponse() " + pCompletionKey + " received, remaining canceled")
            return
        self.responses = True
        self.runningTotal += 1
        print("[Python] ...MyBusinessProcess:OnResponse() " + pCompletionKey + " is called with response: %d and running total: %d" % (callResponse.responseString, self.runningTotal))
        return

    def OnComplete(self, request, response):
        print("[Python] ...MyBusinessProcess:OnComplete() is called with running total: %d\n" % self.runningTotal)
        return