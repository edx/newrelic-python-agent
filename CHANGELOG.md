# Changelog

Releases are named `X.Y.Z+twou-no-report.W` where:

- `X.Y.Z` is the last official version that the commit incorporates
- `W` is a counter starting from 0, reset for each new official version that has been merged in

## 9.11.0+twou-no-report.1 - 2024-07-08

### Added

- Django setting `EDX_NEWRELIC_DISABLE` to entirely stop agent from activating.
- Documentation on existing toggle
- Documentation for testing and releasing

## 9.11.0+twou-no-report.0 - 2024-06-26

### Added

- Django setting `EDX_NEWRELIC_NO_REPORT` to prevent agent from talking to New Relic (but preserve instrumentation).

  If the setting is present and enabled, the agent will not talk to New Relic's servers and will instead use a set of previously captured responses from our sandbox account. Instrumentation (tracing, etc.) will still be in place, but the data will be discarded rather than being reported. See https://github.com/edx/edx-arch-experiments/issues/692 for details.
