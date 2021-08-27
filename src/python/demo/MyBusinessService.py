import pex

class MyBusinessService(pex.BusinessService):
    
    def OnInit(self):
        print("[Python] ...MyBusinessService:OnInit() is called")
        return

    def OnTeardown(self):
        print("[Python] ...MyBusinessService:OnTeardown() is called")
        return

    def OnProcessInput(self, messageInput):
        print("[Python] ...MyBusinessService:OnProcessInput() is called")
        return "received input"