import grongier.pex

class MyLoggingOperation(grongier.pex.BusinessOperation):
    
    def OnInit(self):
        print("[Python] ...MyLoggingOperation:OnInit() is called")
        return

    def OnTeardown(self):
        print("[Python] ...MyLoggingOperation:OnTeardown() is called")
        return

    def OnMessage(self, messageInput):
        print("[Python] ...MyLoggingOperation:OnMessage() is called")
        self.LOGINFO("testing operation logging info")
        self.LOGALERT("testing operation logging alert")
        self.LOGWARNING("testing operation logging warning")
        self.LOGERROR("testing operation logging error")
        self.LOGASSERT("testing operation logging assert")
        return