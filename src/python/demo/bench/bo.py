
import iris
from grongier.pex import BusinessOperation
from msg import MyBenchPickle as msg

class MyBench(BusinessOperation):

    def on_message(self, request):

        dump = request.property_name_0
        dump = request.property_name_1
        dump = request.property_name_2
        dump = request.property_name_3
        dump = request.property_name_4
        dump = request.property_name_5
        dump = request.property_name_6
        dump = request.property_name_7
        dump = request.property_name_8
        dump = request.property_name_9
        # self.log_info(len(request.bina))


        return msg("test")