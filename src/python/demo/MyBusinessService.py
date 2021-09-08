import grongier.pex

class MyBusinessService(grongier.pex.BusinessService):
    
    def OnInit(self):
        print("[Python] ...MyBusinessService:OnInit() is called")
        return

    def OnTeardown(self):
        print("[Python] ...MyBusinessService:OnTeardown() is called")
        return

    def OnProcessInput(self, messageInput):
        msg = "[Python] ...MyBusinessService:OnProcessInput() is called"
        print(msg)
        self.LOGINFO(msg+messageInput)
        return "received input"