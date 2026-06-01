import sys
from pathlib import Path

src_path = Path(__file__).resolve().parents[3] / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from demo import OrderRequest, prod
from iop import Production


PRODUCTIONS = [prod]


def main() -> int:
    runtime_prod = Production.from_iris("Demo.Production")
    print(runtime_prod.graph())
    file_ref = runtime_prod.get_component("FileInput")
    print(f"FileInput component reference: {file_ref}")
    order_ref = runtime_prod.get_component("OrderOperation")
    print(f"OrderOperation component reference: {order_ref}")
    rsp = order_ref.test(OrderRequest(order_id="123"))
    print(f"Test response: {rsp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
