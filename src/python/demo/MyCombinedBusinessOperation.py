import pex
import demo.MyResponse

class MyCombinedBusinessOperation(pex.BusinessOperation):
    
    def OnInit(self):
        self.myInt = int(self.myInt)
        self.myFloat = float(self.myFloat)
        print("[Python] ...MyCombinedBusinessOperation:OnInit() is called")
        print("[Python] ...MyCombinedBusinessOperation has int: %d, float %f, string: %r" % (self.myInt, self.myFloat, self.myString))
        return

    def OnTeardown(self):
        print("[Python] ...MyCombinedBusinessOperation:OnTeardown() is called")
        return

    def OnMessage(self, messageInput):
        # this is called from MyCombinedBusinessProcess which sends an Ens.StringRequest message
        print("[Python] ...MyCombinedBusinessOperation:OnMessage() is called with message: " + messageInput.get("StringValue"))
        tResponse = demo.MyResponse.MyResponse()
        tResponse.responseString = "response from my business operation"
        return tResponse