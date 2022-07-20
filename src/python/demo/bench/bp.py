from grongier.pex import BusinessProcess
from msg import MyBenchPickle as message
import iris

import time

class MyBench(BusinessProcess):

    def on_init(self):
        return

    def on_request(self, request):
        i = 0
        start = time.perf_counter()
        while i<1000:
            i=i+1
            msg = message('property_name_0','property_name_0','property_name_0','property_name_0','property_name_0','property_name_0','property_name_0','property_name_0','property_name_0','property_name_0')

            rsp = self.send_request_sync('Bench.bo.MyBench', msg)
        end = time.perf_counter()
        self.log_info(f"timed : {end-start}")
        return iris.cls('Ens.StringResponse')._New(f"{end-start}")

if __name__ == '__main__':
    bp = MyBench()
    resp = bp._dispatch_on_request('', iris.cls('Ens.Request')._New())
    resp