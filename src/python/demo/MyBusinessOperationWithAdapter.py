import pex

class MyBusinessOperationWithAdapter(pex.BusinessOperation):
    
    def OnInit(self):
        print("[Python] ...MyBusinessOperationWithAdapter:OnInit() is called")
        return

    def OnTeardown(self):
        print("[Python] ...MyBusinessOperationWithAdapter:OnTeardown() is called")
        return

    def OnMessage(self, messageInput):
        # called from ticker service, message is of type MyRequest with property requestString
        print("[Python] ...MyBusinessOperationWithAdapter:OnMessage() is called with message: " + messageInput.requestString)
        self.Adapter.invoke("printString", messageInput.requestString)
        return