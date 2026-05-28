from typing import Annotated

from iop import BusinessService, Category, Setting, controls, setting


def _property(component, name):
    return next(prop for prop in component._get_properties() if prop[0] == name)


def test_setting_descriptor_adds_iris_metadata():
    class Service(BusinessService):
        Target = setting(
            "",
            category=Category.BASIC,
            required=True,
            description="Target component",
            control=controls.production_item(),
        )

    assert _property(Service, "Target") == [
        "Target",
        "String",
        "",
        True,
        "Basic",
        "Target component",
        "selector?context={Ens.ContextSearch/ProductionItems?targets=1&productionName=@productionId}",
    ]


def test_annotated_setting_adds_iris_metadata_without_class_attribute():
    class Service(BusinessService):
        Framing: Annotated[
            str,
            Setting(
                "None",
                category=Category.CONNECTION,
                control=controls.framing(),
            ),
        ]

    assert _property(Service, "Framing") == [
        "Framing",
        "String",
        "None",
        False,
        "Connection",
        "",
        "selector?context={Ens.ContextSearch/getDisplayList?host=@currHostId&prop=Framing}",
    ]


def test_legacy_attr_info_supports_control_metadata():
    class Service(BusinessService):
        Directory = ""

        @staticmethod
        def Directory_info():
            return "/tmp/input"

    Service.Directory_info.__annotations__["return"] = {
        "Category": "Connection",
        "Description": "Input directory",
        "DataType": str,
        "Control": controls.directory(),
    }

    assert _property(Service, "Directory") == [
        "Directory",
        "String",
        "/tmp/input",
        False,
        "Connection",
        "Input directory",
        "directorySelector",
    ]


def test_plain_attributes_keep_default_python_attributes_category():
    class Service(BusinessService):
        BatchSize = 10

    assert _property(Service, "BatchSize") == [
        "BatchSize",
        "Integer",
        10,
        False,
        "",
        "",
        "",
    ]


def test_controls_expose_pythonic_and_raw_selector_strings():
    assert (
        controls.framing()
        == "selector?context={Ens.ContextSearch/getDisplayList?host=@currHostId&prop=Framing}"
    )
    assert controls.directory() == "directorySelector"
    assert controls.raw("selector?context={Custom/Search}") == (
        "selector?context={Custom/Search}"
    )
