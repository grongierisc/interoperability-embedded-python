from iop import BusinessService


class TearDownLifecycleService(BusinessService):
    MarkerPath: str = ""

    def on_tear_down(self):
        with open(self.MarkerPath, "a", encoding="utf-8") as marker:
            marker.write("torn-down\n")
