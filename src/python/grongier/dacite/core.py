from dataclasses import is_dataclass
from typing import TypeVar, Type, Optional, Mapping, Any, Dict

from grongier.dacite.config import Config
from grongier.dacite.data import Data
from grongier.dacite.dataclasses import get_default_value_for_field, create_instance, DefaultValueNotFoundError, get_fields
from grongier.dacite.exceptions import (
    DaciteError,
    UnionMatchError,
    MissingValueError,
    DaciteFieldError,
    StrictUnionMatchError,
)
from grongier.dacite.types import (
    is_instance,
    is_union,
    is_generic_collection,
    extract_origin_collection,
    is_optional,
    make_get_value_transformer,
)

T = TypeVar("T")


def from_dict(data_class: Type[T], data: Data, config: Optional[Config] = None) -> T:
    """Create a data class instance from a dictionary.

    :param data_class: a data class type
    :param data: a dictionary of a input data
    :param config: a configuration of the creation process
    :return: an instance of a data class
    """
    init_values: Dict[str, Any] = {}
    post_init_values: Dict[str, Any] = {}
    unexpected_fields: Dict[str, Any] = {}
    config = config or Config()
    data_class_fields = config.cache.cache(get_fields)(data_class, config.forward_references)
    extra_fields = set(data.keys()) - {f.name for f, _ in data_class_fields}
    for extra_field in extra_fields:
        unexpected_fields[extra_field] = data[extra_field]
    for field, field_type in data_class_fields:
        try:
            try:
                field_data = data[field.name]
                transformed_value = config.cache.cache_from_factory(make_get_value_transformer)(
                    config.type_hooks, config.cast, field_type, type(field_data)
                )(field_data)
                value = _build_value(type_=field_type, data=transformed_value, config=config)
            except DaciteFieldError as error:
                error.update_path(field.name)
                raise
        except KeyError:
            try:
                value = get_default_value_for_field(field)
            except DefaultValueNotFoundError:
                if not field.init:
                    continue
                raise MissingValueError(field.name)
        if field.init:
            init_values[field.name] = value
        else:
            post_init_values[field.name] = value

    return create_instance(data_class=data_class, init_values=init_values, post_init_values=post_init_values, unexpected_fields=unexpected_fields)


def _build_value(type_: Type, data: Any, config: Config) -> Any:
    if is_union(type_):
        return _build_value_for_union(union=type_, data=data, config=config)
    elif is_generic_collection(type_) and isinstance(data, extract_origin_collection(type_)):
        return _build_value_for_collection(collection=type_, data=data, config=config)
    elif config.cache.cache(is_dataclass)(type_) and isinstance(data, Mapping):
        return from_dict(data_class=type_, data=data, config=config)
    return data


def _build_value_for_union(union: Type, data: Any, config: Config) -> Any:
    if is_optional(union) and len(union.__args__) == 2:
        return _build_value(type_=union.__args__[0], data=data, config=config)
    union_matches = {}
    for inner_type in union.__args__:
        try:
            # noinspection PyBroadException
            try:
                transformer = config.cache.cache_from_factory(make_get_value_transformer)(
                    config.type_hooks, config.cast, inner_type, type(data)
                )
                data = transformer(data)
            except Exception:  # pylint: disable=broad-except
                continue
            value = _build_value(type_=inner_type, data=data, config=config)
            if is_instance(value, inner_type):
                if config.strict_unions_match:
                    union_matches[inner_type] = value
                else:
                    return value
        except DaciteError:
            pass
    if config.strict_unions_match:
        if len(union_matches) > 1:
            raise StrictUnionMatchError(union_matches)
        return union_matches.popitem()[1]
    if not config.check_types:
        return data
    raise UnionMatchError(field_type=union, value=data)


def _build_value_for_collection(collection: Type, data: Any, config: Config) -> Any:
    if isinstance(data, Mapping):
        return data.__class__(  # type: ignore
            (key, _build_value(type_=collection.__args__[1], data=value, config=config)) for key, value in data.items()
        )
    return data.__class__(_build_value(type_=collection.__args__[0], data=item, config=config) for item in data)
