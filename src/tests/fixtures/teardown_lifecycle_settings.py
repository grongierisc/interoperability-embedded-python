import os

from teardown_lifecycle_component import TearDownLifecycleService

from iop import Production

TEARDOWN_PRODUCTION = Production(
    "Python.TeardownLifecycleProduction",
    testing_enabled=True,
)
TEARDOWN_PRODUCTION.service(
    "Python.TeardownLifecycleService",
    TearDownLifecycleService,
    class_name="Python.TeardownLifecycleService",
    settings={"MarkerPath": os.environ["IOP_TEARDOWN_MARKER_PATH"]},
)

PRODUCTIONS = [TEARDOWN_PRODUCTION]
