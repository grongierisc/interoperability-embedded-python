import random
import grongier.pex
import demo.SimpleObject

class MyInboundAdapter(grongier.pex.InboundAdapter):
    
    def OnInit(self):
        print("[Python] ...MyInboundAdapter:OnInit() is called")
        self.runningCount=0
        return

    def OnTearDown(self):
        print("[Python] ...MyInboundAdapter:OnTeardown() is called")
        return

    def OnTask(self):
        print("[Python] ...MyInboundAdapter:OnTask() is called")
        if random.random() < 0.5:
            msg = "this is message # %d" %self.runningCount
            self.runningCount += 1
            request = demo.SimpleObject.SimpleObject(msg)
            print("[Python] ...MyInboundAdapter:OnTask() calls ProcessInput() with: " + msg)
            response = self.BusinessHost.ProcessInput(request)
            print("[Python] ...MyInboundAdapter received response: " + response)
        return