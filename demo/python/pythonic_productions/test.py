import sys
from pathlib import Path

src_path = Path(__file__).resolve().parents[3] / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from demo import OrderRequest
from iop import Production


prod = Production.from_iris("Demo.Production")

print(prod.graph())

rsp = prod.test("FileInput.Output", OrderRequest(order_id="123"))
print(rsp)



