# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.1.0] - 2026-07-16
### Changed
- Move remote debugging support to the optional `debug` extra. Install
  `iris-pex-embedded-python[debug]` before enabling debugpy integration.
- Standardize contributor verification through the `dev` extra and tox.
- Publish packages only from explicit releases after verification.
- Update the default `PersistentMessage` schema mode from `extend` to `managed`
  for compatibility with `iris-persistence` 0.3.

### Fixed
- Make CLI mocks resolve consistently on Python 3.10 when `iop.cli.main` is
  also exposed as the public CLI function.
- Preserve pytest's real exit status when preview IRIS changes the process
  status during Embedded Python interpreter shutdown.

### Internal
- Add wheel-content and installed-ObjectScript validation.
- Refactor persistent-message resolution and production/migration internals
  without changing their public interfaces.

## [4.0.1] - 2026-06-29
### Added
- Add default target support to `target(...)`, allowing `target("OperationName")` to populate the generated setting initial expression, production Host setting, and graph edge once the named target item exists.
- Allow `ComponentRef.connect(...)` to accept class-declared `target()` descriptors, supporting static-friendly calls such as `rest.connect(Rest.Output, operation)`.
- Add package typing metadata with `py.typed` and explicit `ComponentRef` return annotations for production factory methods.

### Fixed
- Expose declared and manual target settings through `dir(ComponentRef)` so `rest.my_target` style graph handles are discoverable by runtime autocomplete.
- Validate target setting values that reference missing production items.
- Normalize `setting(...)` and `target(...)` descriptors used as production setting keys before validation and IRIS rendering.
- Improve component registration failures during migration with targeted guidance for missing IoP support classes and container startup races.
- Render generated instance-style Python routes with `component.connect(...)`.
- Refactor business process and operation message dispatch around normalized message keys for `@handler`, typed methods, legacy `DISPATCH`, and native IRIS requests.

## [4.0.0] - 2026-06-21
### Breaking Changes
- Remove the legacy `grongier.pex` compatibility package and `Grongier.PEX` ObjectScript classes. Use `iop` and `IOP.*` classes instead.
- Rename Python component lifecycle hooks to snake_case, including `on_init`, `on_message`, and `on_process_input`.
- Move implementation modules from private `iop._*` files into package namespaces such as `iop.components`, `iop.messages`, `iop.migration`, `iop.production`, and `iop.runtime`.
- Remove the legacy WSGI helper classes and package metadata from `setup.py`; project metadata is now managed from `pyproject.toml`.

### Added
- Add `PollingBusinessService` for `iop` to create scheduled polling business services without manually returning `Ens.InboundAdapter`.
- Add `iop --migrate --dry-run` / `--explain` to print and validate the migration plan without writing to IRIS.
- Add Pythonic component setting metadata with `setting(...)`, `Setting`, `Category`, and `controls` helpers for IRIS production categories, descriptions, required flags, and editor controls.
- Add `Production` module: a Python DSL for authoring, importing, diffing, and managing IRIS interoperability production topology entirely from Python. Declare components, ports, and routing with `service()`, `operation()`, `process()`, `connect()`, and `connect_add()`; drive the full production lifecycle (`start`, `stop`, `restart`, `test`, `diff`, `apply`); and export the topology as a typed graph (`ProductionGraph`, `GraphEdge`, `GraphNode`).
- Add production reconstruction and rendering support to import productions from IRIS, rebuild them from dictionaries, export them as JSON, XML, Python drafts, or graph data, and include runtime connections and queue information.
- Add runtime director abstractions for local and remote IRIS management, including namespace-aware production control, component start/stop/restart, queue inspection, runtime connection export, and `DirectorProtocol`.
- Add REST endpoints for production connections, queue information, component lifecycle actions, and IOP-generated proxy class bindings.
- Add CLI support for export formats with `--format json|python|graph`, remote settings files with `-R/--remote-settings`, `--bindings`, `--unused`, and `--unbind`.
- Add public binding helpers: `bind_component`, `unbind_component`, `list_bindings`, `register_component`, and `unregister_component`.
- Add `@handler(MessageType)` for explicit business operation and business process message dispatch; duplicate mappings now emit a warning that identifies the discarded handler.
- Add support metadata for Python 3.13 and 3.14.

### Changed
- Register `PollingBusinessService` classes through package/file migration.
- Improve migration output and validation for common message registration mistakes.
- Include mode, namespace, and a final success line in migration output.
- Refactor the CLI into dedicated parser, formatting, and type modules.
- Refactor remote runtime support into dedicated client, director, migration, settings, and setup modules.
- Improve production object migration by automatically registering referenced component, adapter, and `PersistentMessage` classes with deduplication.
- Improve business host connection discovery and message serialization error handling.
- Improve service hook ergonomics: `BusinessService.on_process_input()` now delegates to `on_message()`, and `PollingBusinessService` now recommends `on_poll()` for scheduled polling.
- Update demos, tests, and documentation to use the `iop` package layout, snake_case hooks, and Pythonic production definitions.

### Deprecated
- Deprecate the static `iop.Utils` / `iop.migration.utils._Utils` facades in favor of functions in `iop.migration.utils`; these facades are scheduled for removal in v5.0.
- Deprecate the static `iop.Director` / `iop.runtime.director._Director` facades in favor of functions in `iop.runtime.director`; these facades are scheduled for removal in v5.0.
- Deprecate silent default no-op handlers for unimplemented `on_message()`, `on_process_input()`, and `on_poll()` hooks; they now warn and are scheduled to raise in v5.0.

### Fixed
- Fix production graph edge assertions and runtime connection handling to match the new graph structure.
- Fix production lifecycle and migration error handling for local and remote execution paths.
- Fix component connection discovery so inspection does not execute component initialization hooks.
- Fix message dispatch for postponed annotations and native IRIS message annotations such as `"iris.Ens.StringRequest"`.

## [3.7.1] - 2026-05-28
### Added
- Add native `PersistentMessage` support backed by `iris-persistence`, including `CLASSES` registration, native IRIS message body materialization, class-parameter based deserialization, and default `Ens.MessageBody` schema generation in extend mode.
- Export `Model` from `iop` for nested native persistent or serial objects inside `PersistentMessage`.

### Fixed
- Fix `PersistentMessage` deserialization for IRIS-originated messages whose Python module is not already importable by storing and using `IOP_PYTHON_CLASSPATH`.
- using ruff to fix various linting issues and improve code quality

### Changed
- Optimize `PersistentMessage` dispatch by caching IRIS classname to Python class resolution and avoiding repeated IRIS wrapper checks on the native message hot path.

## [3.6.1] - 2026-05-12
### Fixed
- Fix json schema handling enums.

## [3.6.0] - 2026-03-30
### Added
- `iop` command line has a new full remote controle feature, allowing to start, stop, restart, update, test and log productions on a remote IRIS instance through its REST API
  
### Fixed
- Review how sys.path is updated by Common.cls to ensure it works correctly in all environments

### Changed
- Refactor whole unittest and e2e test suite for better maintainability and reliability
- Export production now returns Production name as key in the returned dict for better clarity
- Prevent dataclass and pydantic messages from being serialized with the same serializer as regular messages, to avoid issues with dataclass fields and pydantic validation

## [3.5.5] - 2026-01-23
### Added
- Add `iop --update` command to update a production from the command line
- New info displayed in `iop --help` command showing current namespace
- `iop --status` command now shows if production needs update, if so a message is displayed
- Command line option `--namespace` alone will show the current namespace

### Fixed
- Fix issue with boolean `response_required` parameter in `send_request_async` method of BusinessProcess
  - Now converts boolean to integer (1 or 0) to ensure compatibility with IRIS API

## [3.5.4] - 2025-11-25
### Added
- new option for migrate `--force-local` to force local migration even if remote url is provided in the `settings.py` file
- `verify_ssl` option in `settings.py` to enable or disable SSL verification for remote migration

### Fixed
- Fix an error when running `iop` command without a valid iris instance available
  - Now it will log a warning instead of raising an exception
- Support purging old messages in production settings

## [3.5.3] - 2025-08-01
### Fixed
- Fix a regression test message interoperability where list of messages was not displayed correctly in the UI
  - This was caused by MessageHandler changes in version 3.5.1
- Minor fixes for remote migration support

## [3.5.2] - 2025-08-01
### Added
- Remote migration support, allowing importing Python IOP modules into IRIS through `http`

## [3.5.1] - 2025-07-22
### Added
- New IOP.Wrapper class for simplified python module import into IRIS with remote debugging support and traceback handling
 
### Changed
- Improve module loading and initialization for better performance in BusinessProcess by checking if the module is already loaded
- Change OnMessage to MessageHandler in BusinessOperation for better performance and clarity

## [3.5.0] - 2025-06-30
### Added
- Initial support for venv
- New `send_generator_request` method in `iop` module to send generator requests
- Add `get_iris_id` method to `Message*` classes to retrieve the IRIS ID of a message

### Fixed
- Fix `iris.*` function dispatch mapping

## [3.4.4] - 2025-06-13
### Added

### Changed
- `%traceback` setting default value is now `True` to show traceback in message log
- serializer is now more permissive for iris objects, allowing iris object type of `%Stream` to support http inbound/outbound adapters
- remove usage of `pkg_resources` in favor of `importlib.resources`
- refactor import statements for better clarity and organization

### Fixed
- fix typing issues in python code
- fix long string attribute from production settings ( greater than 255 characters )

## [3.4.3] - 2025-05-26

### Fixed
- Fix a regression in DTL to display sub-objects
- Improve upgrade compatibility with 3.4.0 (pre-debugger)

### Changed
- Change debugger settings to be prefixed with `%` to avoid conflict with other settings

### Added
- Add `%traceback` setting to enable or disable traceback in message log

## [3.4.2] - 2025-05-2
### Fixed
- Fix regression in version 3.4.0 and 3.4.1 where production settings were not properly loaded

## [3.4.1] - 2025-04-30

### Added
- Add namespace selection in the `iop` command
  - `-n` or `--namespace` option to select a namespace
- Initial remote debugging support

### Changed
- Change how `iris` module is loaded
  - Create a new `_iris` module in the `iop` package
- Remove dependency on community driver
  - Use `iris` module instead

### Fixed
- Fix dataclass message serialization
  - Go back to best effort serialization : type check is not forced
  - For checking use PydanticMessage
- Logger now uses the correct level for `debug`, `info` and similar methods

## [3.4.0] - 2025-03-24

### Added
- Support for production settings configuration and management
- Enhanced Python logging integration with IRIS
- Support for schema registration with PydanticMessage
- Improved Pydantic integration for message validation
- Logger property in _Common class for better logging management

### Changed
- Refactored _director and _utils modules
- Enhanced serialization module
  - Simplified type conversion
  - Improved Pydantic integration
  - Removed deprecated methods
  - Remove dacite and dc-schema dependencies in favor of Pydantic
- Improved logging mechanism
  - Encapsulated console logging behavior
  - Enhanced logger initialization
- Updated pytest configuration for asyncio

### Fixed
- Fixed log handling in Command class
- Improved error handling in OnGetConnections method

## [3.3.0] - 2025-01-25

### Added
- Support of Pydantic message validation and serialization
- Enhanced Python logging integration with LogManager
- New test framework with pytest-asyncio support
- Improved error handling and validation

### Changed
- Refactored core components for better maintainability
- Enhanced message serialization system
- Improved production settings handling

### Fixed
- Various log handling issues
- Message validation edge cases

## [3.2.0] - 2025-01-15

### Added
- DTL (Data Transformation Layer) with JSON Schema support
- Complex JSON transformation capabilities
- Enhanced documentation for DTL features
- JsonPath support for data manipulation
- Comprehensive schema validation system

### Changed
- Improved message transformation handling
- Enhanced error reporting for schema validation
- Refactored transformation engine

### Fixed
- JSON Schema processing issues
- Array handling in transformations
- Various DTL edge cases

## [3.1.0] - 2024-07-26

### Added
- Async function support in Business Processes and Operations
- Multi-sync call capabilities
- Enhanced trace logging options
- New benchmarking tools
- Improved session handling

### Changed
- Refactored business host dispatch system
- Enhanced message serialization
- Improved async request handling

### Fixed
- Retro-compatibility with grongier.pex
- Session management issues
- Various async operation bugs

## [3.0.0] - 2024-07-08

### Changed
- Renamed package from grongier.pex to iop
- Major refactoring of core components
- Improved package structure
- Enhanced documentation

### Added
- New installation methods
- Better package management
- Improved error handling

## [2.3.24] - 2024-03-08

### Added
- Dev mode support for WSGI applications
- Experimental iris module features
  - Sugar syntax for common operations
  - Enhanced intellisense support
- Improved WSGI configuration options

### Fixed
- PyPI version synchronization
- WSGI handling issues
- Device redirection in WSGI

## [2.3.20] - 2023-12-13

### Fixed
- Fix upgrade version issues

## [2.3.19] - 2023-12-12

### Added
- Support for OnGetConnections and on_get_connections to show connections between components in interoperability UI

## [2.3.18] - 2023-12-11

### Fixed
- Named argument not serialized for send_request_sync and send_request_async

## [2.3.17] - 2023-11-24

### Added
- Support relative path for migration

## [2.3.16] - 2023-10-30

### Added
- Support of Japanese characters
- New command line options
  - Logs number of line
  - Start production async

## [2.3.12] - 2023-10-04

### Added
- New command line option test

### Changed
- Refactored some code

### Fixed
- Various minor fixes

## [2.3.8] - 2023-07-13

### Fixed
- iop --init command
- cls compilation with zpm

## [2.3.7] - 2023-07-07

### Fixed
- Source dir and package for zpm

## [2.3.6] - 2023-07-07

### Fixed
- ZPM installation

## [2.3.5] - 2023-07-05

### Added
- Initial WSGI support
- Settings.py support

### Changed
- Aligned version with pypi

## [2.3.0] - 2023-05-31

### Added
- Command line support
- Settings.py files support

## [2.2.0] - 2023-05-19

### Added
- Manager support for production management
  - Settings.py class support for component and production configuration
  - Director support for production control and logging

## [2.1.0] - 2023-04-21

### Added
- Support for Python 3.6 (RedHat 8.x)
- Deployment with PyPi

### Fixed
- Files and folders named with "_"
- Stronger check on Message

## [2.0.0] - 2023-03-15

### Added
- Iop command line
