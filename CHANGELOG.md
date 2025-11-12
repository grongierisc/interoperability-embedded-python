# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
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
