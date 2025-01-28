import asyncio
import random

from iop import BusinessProcess
from msg import MyMessage


class MyAsyncNGBP(BusinessProcess):

    def on_message(self, request):

        results = asyncio.run(self.await_response(request))

        for result in results:
            self.logger.info(f"Received response: {result.message}")

        return MyMessage(message="All responses received")

    async def await_response(self, request):
        # create 1 to 10 messages
        tasks = []
        for i in range(random.randint(1, 10)):
            tasks.append(self.send_request_async_ng("Python.MyAsyncNGBO",
                                                    MyMessage(message=f"Message {i}")))

        return await asyncio.gather(*tasks)

