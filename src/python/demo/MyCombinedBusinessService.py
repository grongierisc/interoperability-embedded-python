import pex
import MyRequest

class MyCombinedBusinessService(pex.BusinessService):
	
	def OnInit(self):
		self.min = int(self.min)
		self.max = int(self.max)
		StringValue="[Python] ...MyCombinedBusinessService:OnInit() is called with min: %d and max: %d" % (self.min, self.max)
		print(StringValue)
		self.LOGINFO(StringValue)
		self.LOGINFO("Service OnInit")
		self.LOGINFO("min %d" % self.min)
		self.LOGINFO("max %d" % self.max)
		self.mid = 0.5*(self.min + self.max)
		self.LOGINFO("mid %d" % self.mid)
		print("[Python] ...MyCombinedBusinessService:OnInit() has mid: %d" % self.mid)
		return

	def OnTeardown(self):
		StringValue="[Python] ...MyCombinedBusinessService:OnTeardown() is called"
		print(StringValue)
		self.LOGINFO(StringValue)
		self.LOGINFO("Service OnTeardown")
		return

	def OnProcessInput(self, messageInput):
		StringValue="[Python] ...MyCombinedBusinessService:OnProcessInput() is called"
		print(StringValue)
		self.LOGINFO(StringValue)
		self.LOGINFO("Service OnProcessInput")
		tRequest = MyRequest.MyRequest()
		tRequest.requestString = "request from my business service"
		self.SendRequestAsync("Grongier.PEX.BusinessOperation", tRequest)
		return