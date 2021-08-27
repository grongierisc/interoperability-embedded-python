import pex
import MyResponse  

class MyBusinessOperation(pex.BusinessOperation):
    
    def OnInit(self):
        print("[Python] ...MyBusinessOperation:OnInit() is called")
        return

    def OnTeardown(self):
        print("[Python] ...MyBusinessOperation:OnTeardown() is called")
        return

    def OnMessage(self, messageInput):
        # called from ticker service, message is of type MyRequest with property requestString
        self.LOGINFO("Operation OnMessage")
        print("[Python] ...MyBusinessOperation:OnMessage() is called with message: " + messageInput.StringValue)
        # print("[Python] ...MyBusinessOperation:OnMessage() is called with message: " + messageInput.get("StringValue"))
        response = MyResponse.MyResponse("...MyBusinessOperation:OnMessage() echos")
        return response