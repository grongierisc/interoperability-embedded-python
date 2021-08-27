import iris
import pex

if __name__ == "__main__":
    connection = iris.createConnection(hostname="localhost", port=51773, namespace="ENSEMBLE",username="_SYSTEM",password="SYS")
    service = iris.pex.Director.CreateBusinessService(connection, "Demo.PEX.NonPollingBusinessService")
    response = service.ProcessInput("request from non polling starter")
    print(response)
