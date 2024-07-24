import asyncio
import sys,os 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')))
from iop import BusinessProcess
from msg import MyMessage


class MyAsyncNGBP(BusinessProcess):

    def on_message(self, request):
        import time
        start_time = time.time()
        results = asyncio.run(self.await_response(request))
        end_time = time.time()
        print(f"Time taken: {end_time - start_time} seconds")
        self.log_info(f"Time taken: {end_time - start_time} seconds")
        for result in results:
            print(f"Received response: {result.message}")

    async def await_response(self, request):
        msg_one = MyMessage(message="Message1")
        msg_two = MyMessage(message="Message2")

        # use asyncio.gather to send multiple requests asynchronously
        # using the send_request_async_ng method
        tasks = [self.send_request_async_ng("Python.MyAsyncNGBO", msg_one, timeout=5),
                 self.send_request_async_ng("Python.MyAsyncNGBO", msg_two, timeout=-1)]

        return await asyncio.gather(*tasks)

if __name__ == "__main__":
    bp = MyAsyncNGBP()
    bp.on_message(None)
