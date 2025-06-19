from typing import Any
from iop import BusinessOperation

from msg import MyGeneratorResponse, MyGenerator

from intersystems_iris.dbapi._DBAPI import connect
import openai

class MyGeneratorOperation(BusinessOperation):

    def on_init(self) -> None:
        self._conn = connect(
            embedded=True,
        )

    def on_private_session_started(self, request: MyGenerator) -> Any:
        sql = """SELECT TOP 10
                ID, StringValue
                FROM Ens.StringRequest"""

        return self.my_generator(sql)

    def my_generator(self, sql) -> Any:
        cursor = self._conn.cursor()
        cursor.execute(sql)
        for row in cursor:
            yield MyGeneratorResponse(
                my_other_string=row[1]
            )

    def on_openai_streaming(self, request: 'msg.MyOtherGeneratorCall') -> Any:
        client = openai.OpenAI(api_key="your-api-key-here")
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.StringValue}
            ],
            stream=True
        )
        return self._my_openai_gen(response)
    
    def _my_openai_gen(self, response) -> Any:
        for event in response:
            yield MyGeneratorResponse(
                my_other_string=event.to_json()
            )
    