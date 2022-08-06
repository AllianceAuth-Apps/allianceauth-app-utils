# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

## [1.14.1] - 2022-08-06

### Changed

- Improve EveOnline test factories
- Adopt tox tests for AA3

## [1.14.0] - 2022-07-21

### Added

- Testdata factories generated with Factory Boy: `testdata_factories`

## [1.13.1] - 2022-06-18

### Changed

- Add wheel to PyPI deployment

## [1.13.0] - 2022-03-02

### Added

- allianceauth.get_redis_client(): Return the current redis client used for Django caching and works with the new and old django redis caching library

## [1.12.0] - 2022-03-02

### Added

- Support for Django 4.0 & Python 3.10

## [1.11.0] - 2022-02-16

### Added

- testing: New factory methods for test objects of Group, State, EveCharacter

### Fixed

- testing.add_new_token(): Will now create identical character owner hash for additional tokens of the same character to prevent owner revocation by Auth

## [1.10.0] - 2022-01-31

### Added

- New features that make it much easier to create an ESI client stub individually for each test, e.g. endpoints can be defined with testdata or side effects for each test

### Changed

- Remove support for Python 3.6
- Improve request logic for esi status

## [1.9.0] - 2021-12-22

### Added

- default_if_none()

## [1.8.2] - 2021-10-29

### Fixed

- fetch_esi_status() aborts with exception on connection timeout and connect errors

## [1.8.1] - 2021-10-29

### Changed

Added tests for AA 2.9 / Django 3.2 to CI

### Fixed

- Class `HttpResponseNoContent` did not work with Django 3.2

## [1.8.0] - 2021-07-14

### Added

- `esi.retry_task_if_esi_is_down`: Retry current celery task if ESI is not online or error threshold is exceeded.
- `views.JSONResponseMixin`: A mixin that can be used to render a JSON response for a class based view.

### Changed

- Deprecated: `allianceauth.create_fake_user`. Use `testing.create_fake_user` instead.
- Deprecated: `testing.BravadoOperationStub`. Use `esi_testing.BravadoOperationStub` instead.
- Deprecated: `testing.BravadoResponseStub`. Use `esi_testing.BravadoResponseStub` instead.

## [1.7.1] - 2021-07-01

### Changed

- Renamed `APP_UTILS_ADMIN_NOTIFY_TIMEOUT` to `APP_UTILS_NOTIFY_THROTTLED_TIMEOUT`

## [1.7.0] - 2021-07-01

### Added

- `helpers.throttle`: Allows calling any function throttled, e.g. to once per day
- `allianceauth.notify_throttled`: Send notification throttled, e.g. to once a day only

## [1.6.0] - 2021-06-29

### Changed

- esi.fetch_esi_status() will not report ESI as down during the daily downtime by default
- messages.messages_plus: Disabled icon feature, since it is not provided by Auth core. Icons will still be rendered, but are now created by Auth (with allianceauth>=2.8.5).

## [1.5.0] - 2021-06-26

### Added

- New section esi containing helpers for working with ESI

### Changed

- Improved documentation with a short summary for each section.
- Logging from this package will now include it's full verbose name

## [1.4.0] - 2021-06-24

### Added

- allianceauth.create_fake_user
- allianceauth.notify_admins_throttled
- views.HttpResponseNoContent

### Changed

- Improved documentation layout

## [1.3.0] - 2021-05-06

### Added

- helpers.humanize_number

## [1.2.0] - 2021-04-16

### Added

- helpers.AttrDict: Access dict like an object
- views.BootstrapStyle
- views.fontawesome_modal_button_html

### Changed

- Performance improvement for django.users_with_permission

### Fixed

- Create TZ aware timestamps in fake ESI response

## [1.1.0] - 2021-03-19

### Added

- testing.create_user_from_evecharacter
- esi_testing module with tools for testing with django-esi
- testing: response_text, json_response_to_python, json_response_to_dict, multi_assert_in, multi_assert_not_in

## [1.0.2] - 2021-03-13

### Changed

- urls.reverse_absolute now also accepts args

## [1.0.1] - 2021-02-27

### Changed

- Improved API documentation
- Restructured test modules

### Fixed

- testing.add_character_to_user_2 not returning EveCharacter

## [1.0.0] - 2021-02-20

### Added

- API documentation on readthedocs

## [1.0.0a7] - 2021-02-18

### Added

- allianceauth.is_night_mode
- django.admin_boolean_icon_html

## [1.0.0a6] - 2021-02-14

### Added

- datetime.ldap_time_2_datetime
- datetime.ldap_timedelta_2_timedelta

## [1.0.0a5] - 2021-02-14

### Added

- allianceauth.notify_admins
- urls.reverse_absolute
- urls.static_file_absolute_url

### Changed

- datetime.timeuntil_str: added show_seconds argument

## [1.0.0a4] - 2021-02-11

### Fixed

- bootstrap labels are spans

## [1.0.0a3] - 2021-02-10

### Changed

- `django.users_with_permission` now also returns superusers by default

## [1.0.0a1] - 2021-02-09

### Added

- Initial
