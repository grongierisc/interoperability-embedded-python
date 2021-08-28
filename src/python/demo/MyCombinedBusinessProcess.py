import iris
import grongier.pex
import demo.MyResponse

class MyCombinedBusinessProcess(grongier.pex.BusinessProcess):
    
    def OnInit(self):
        self.val1 = float(self.val1)
        self.val2 = float(self.val2)
        print("[Python] ...MyCombinedBusinessProcess:OnInit() is called with val1: %f and val2: %f" % (self.val1, self.val2))
        print("[Python] ...MyCombinedBusinessProcess:OnInit() has val3: " + self.val3)
        return

    def OnTearDown(self):
        print("[Python] ...MyCombinedBusinessProcess:OnTeardown() is called")
        return

    def OnRequest(self, request):
        # called from MyCombinedBusinessService with request type MyRequest
        print("[Python] ...MyCombinedBusinessProcess:OnRequest() is called with request: " + request.requestString)
        native = iris.GatewayContext.getIRIS()
        tRequest = native.classMethodObject("Ens.StringRequest", "%New", "request from my business process")
        self.SendRequestAsync("MyCombinedBusinessOperation", tRequest, True, "request # 1")

        tResponse = demo.MyResponse.MyResponse()
        tResponse.responseString = "business process response"
        return tResponse

    # responses from MyCombinedBusinessOperation, which sends type MyResponse as a response
    def OnResponse(self, request, response, callRequest, callResponse, pCompletionKey):
        print("[Python] ...MyCombinedBusinessProcess:OnResponse() " + pCompletionKey + " is called with response: "+ callResponse.responseString)
        return response

    def OnComplete(self, request, response):
        print("[Python] ...MyCombinedBusinessProcess:OnComplete() is called with request: " + request.requestString + ", and response: " + response.responseString + "\n")
        self.Reply(response)
        return response