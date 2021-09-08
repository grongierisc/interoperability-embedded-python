import grongier.pex
import iris

class MyCombinedBusinessOperation(grongier.pex.BusinessOperation):
    
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
        print("[Python] ...MyCombinedBusinessOperation:OnMessage() is called with message: " + messageInput.StringValue)
        tResponse = iris.cls("Ens.StringResponse")._New(" message : "+messageInput.StringValue)
        return tResponse