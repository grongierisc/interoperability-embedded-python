import grongier.pex

class MyBusinessOperationWithIrisAdapter(grongier.pex.BusinessOperation):
    
    def OnInit(self):
        print("[Python] ...MyBusinessOperationWithIrisAdapter:OnInit() is called")
        return

    def OnTeardown(self):
        print("[Python] ...MyBusinessOperationWithIrisAdapter:OnTeardown() is called")
        return

    def OnMessage(self, messageInput):
        # called from ticker service, message is of type MyRequest with property requestString
        print("[Python] ...MyBusinessOperationWithIrisAdapter:OnMessage() is called with message: " + messageInput.StringValue)
        try:
            self.Adapter.PutString(messageInput.StringValue,"hello")
        except Exception as e :
            msg =""
            if hasattr(e, 'message'):
                msg = e.message
            else:
                msg = e
            self.LOGERROR("catch" + str(msg))
        return

    def getAdapterType():
        """
        Name of the registred adaptor
        """
        return "EnsLib.File.OutboundAdapter"