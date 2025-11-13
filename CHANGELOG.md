# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

## [1.28.0] - 2025-11-13

### Added

- `testing.CacheFake`: A fake for replacing Django's cache in tests
- `testing.reset_celery_once_locks`: Function for deleting celery once locks

### Changed

- `esi.retry_task_on_esi_error_and_offline`: Will now also retry when the rate limit is exceeded
- `esi_testing.build_http_error` now also accepts headers.

## [1.27.0] - 2025-10-12

### Added

- `esi.retry_task_on_esi_error_and_offline`: Context manager that retries a task when the error error limit has been exceeded or when ESI appears to be offline

### Changed

- BREAKING CHANGE: Due to [recent changes](https://developers.eveonline.com/blog/hold-your-horses-introducing-rate-limiting-to-esi) of the ESI status endpoint the error count feature no longer works and has been removed. Consequently, `esi.ESIStatus` now only reports whether ESI is online and no longer knows about error limit counts. Related properties have been kept in place for backwards compatibility, but no longer return any values. Related properties and the `esi.EsiErrorLimitExceeded` exception have been deprecated and will be removed in future version.

## [1.26.1] - 2025-07-27

### Fixed

- EsiClientStub x-pages error (#3) - Big thanks to @Geuthur for finding and fixing this bug.

## [1.26.0] - 2025-04-14

### Added

- Class for Bootstrap styles: `views.BootstrapStyleBS5`
- Adds support for Python 3.12

### Changed

- Deprecated: `views.BootstrapStyle`
- Deprecated: `views.fontawesome_modal_button_html`

## [1.25.0] - 2023-12-14

### Added

- New helper function that makes it very easy to use Django in a normal Python script: `scripts.start_django()`

## [1.24.0] - 2023-11-28

### Added

- Added support for AA4

## [1.23.0] - 2023-11-14

### Added

- Setting to disable object cache in tests

## [1.22.0] - 2023-11-08

### Changed

- Improved: `urls.static_file_absolute_url()`
- Improved: `testdata_factories.EveCorporationInfoFactory`

## [1.21.0] - 2023-09-17

### Added

- `views.bootstrap_icon_plus_text_html()`: Improved variant of bootstrap_icon_plus_name_html, which no longer uses nbsp for spacing. Instead a class is provided to enable spacing via CSS styles.

### Changes

- Deprecated: `views.bootstrap_icon_plus_name_html()`

### Fixed

- `views.nowrap_html()` does not work

## [1.20.1] - 2023-09-17

### Changed

- ObjectCacheMixin.clear_cache() now clears all cached objects including variants with select_related

### Fixed

- Incorrect cache key generated in ObjectCacheMixin

## [1.20.0] - 2023-09-17

### Added

- caching: Ability to clear a cached object explicitly

### Changed

- Refactoring based on issues identified by pylint

## [1.19.1] - 2023-07-12

### Fixed

- EsiErrorLimitExceed exception can not be pickled by celery

## [1.19.0] - 2023-06-23

### Changed

- Migrated build process to PEP 621
- Removed support for AA 2 / Django 3
- Added support for Python 3.11

## [1.18.1] - 2023-06-19

### Changed

- Can now define a custom HTTP error exception with EsiStub
- Reworked docs page

## [1.18.0] - 2023-04-27

### Added

- `testrunners.TimedTestRunner`: Custom test runner that can add duration measurements to all tests and shows slowest tests in a summary

### Changed

- Improved type annotations

## [1.17.1] - 2023-03-27

### Changed

- Added status_code and reason to BravadoResponseStub
- Now returning same BravadoResponseStub instead of replaced ResponseStub from BravadoOperationStub

## [1.17.0] - 2023-03-21

### Added

- `EsiStatus.raise_for_exception()` now raises `EsiDailyDowntime` so apps can differentiate normal offline vs. regular offline during daily downtime period. `EsiDailyDowntime` is a sub class of `EsiOffline`, so apps checking just for the later will not be affected

## [1.16.0] - 2023-03-14

### Added

- admin.FieldFilterCountsMemory: Filter by field and show counts for admin site
- admin.FieldFilterCountsDb: Filter by field and show counts for admin site
- database.TableSizeMixin: Add a table size functionality to a Django Manager
- Docs now support auto dark mode

### Changed

- Moved module description from docs to each module as doc string

## [1.15.0] - 2023-02-16

### Added

- You can now specify a custom owner hash when creating character tokens (@Maestro-Zacht)

### Changed

- Removed support for Python 3.7
- Different generator for alliance and corporation name that hopefully create less duplicates

## [1.14.2] - 2022-08-14

### Fixed

- EsiEndpoint can not be created with empty test data

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
