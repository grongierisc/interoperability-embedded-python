import grongier.pex
import iris
import MyResponse

class MyBusinessOperation(grongier.pex.BusinessOperation):
    
    def OnInit(self):
        print("[Python] ...MyBusinessOperation:OnInit() is called")
        self.LOGINFO("Operation OnInit")
        return

    def OnTeardown(self):
        print("[Python] ...MyBusinessOperation:OnTeardown() is called")
        return

    def OnMessage(self, messageInput):
        # called from ticker service, message is of type MyRequest with property requestString
        print("[Python] ...MyBusinessOperation:OnMessage() is called with message:")
        self.LOGINFO("Operation OnMessage")
        # print("[Python] ...MyBusinessOperation:OnMessage() is called with message: " + messageInput.requestString)
        response = MyResponse.MyResponse("...MyBusinessOperation:OnMessage() echos")
        return response