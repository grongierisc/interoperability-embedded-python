import bp
from bo import FileOperation, MySettingOperation
from bs import RedditService
from iop import Production
from message import SimpleMessage, PostMessage

SCHEMAS = [SimpleMessage, PostMessage]

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FilterPostRoutingRule': bp.FilterPostRoutingRule,
    'Python.bp': bp,
    'Python.FileOperation': FileOperation,
}

EMPTY_PRODUCTION = Production("dc.Python.Production", testing_enabled=True)

TEST_SETTING_PRODUCTION = Production(
    "Python.TestSettingProduction",
    testing_enabled=True,
)
TEST_SETTING_OPERATION = TEST_SETTING_PRODUCTION.operation(
    "UnitTest.MySettingOperation",
    MySettingOperation,
    class_name="UnitTest.MySettingOperation",
    settings={
        "my_int_var": 1,
        "my_float_var": 1.0,
        "my_untyped_var": 1,
        "my_str_var": "bar",
    },
)

PRODUCTIONS = [
    EMPTY_PRODUCTION,
    TEST_SETTING_PRODUCTION,
]
