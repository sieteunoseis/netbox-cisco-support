# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.4] - 2025-01-23

### Added

- **Known Bugs Card (Keyword Search)** - Shows high-severity bugs (1-3) for the device type model
- **Version-Specific Bugs Card** - Shows bugs affecting the device's software version using `cc_series` custom field or product ID
- **Stack Coverage Display** - Shows coverage status for all stack members when device serial contains multiple serials
- Comma-separated serial number parsing for switch stacks
- "No critical bugs found" indicator when bug searches return empty results

### Changed

- Optimized database queries with `select_related()` for better performance
- Bug severity filtering done client-side (Cisco API severity parameter causes 500 errors)
- Improved template layout with collapsible cards for each data section

## [1.0.3] - 2025-01-22

### Fixed

- Fixed template packaging for PyPI distribution

## [1.0.2] - 2025-01-21

### Changed

- Renamed PyPI package to `netbox-cisco-support-api` (original name was taken)

## [1.0.1] - 2025-01-21

### Fixed

- Code formatting with black and isort for CI compliance

## [1.0.0] - 2025-01-21

### Added

- **Product Information**
  - Serial number-based product lookup
  - Product name, ID (PID), series, and category display
  - Orderable status indicator
  - Link to Cisco product support page

- **End-of-Life (EoX) Status**
  - End of Sale date
  - End of Software Maintenance date
  - End of Security Support date
  - Last Date of Support
  - Migration product recommendations

- **Security Advisories (PSIRT)**
  - Security advisories affecting the product
  - Severity badges (Critical, High, Medium, Low)
  - CVE references
  - Links to Cisco Security Advisory pages

- **Known Bugs**
  - Critical bugs (severity 1-3) for the product
  - Severity and status indicators
  - Links to Cisco Bug Search

- **Software Recommendations**
  - Suggested software releases from Cisco API

- **Configuration**
  - Configurable manufacturer pattern (regex)
  - API timeout and cache duration settings
  - Settings page with connection test

### Technical

- Built for NetBox 4.0+ (not compatible with NetBox 3.x)
- Python 3.10+ required
- OAuth2 client credentials authentication
- API response caching via Django cache framework
- Apache 2.0 license

[Unreleased]: https://github.com/sieteunoseis/netbox-cisco-support/compare/v1.0.4...HEAD
[1.0.4]: https://github.com/sieteunoseis/netbox-cisco-support/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/sieteunoseis/netbox-cisco-support/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/sieteunoseis/netbox-cisco-support/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/sieteunoseis/netbox-cisco-support/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/sieteunoseis/netbox-cisco-support/releases/tag/v1.0.0
