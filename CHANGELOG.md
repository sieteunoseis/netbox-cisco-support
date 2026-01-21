# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/sieteunoseis/netbox-cisco-support/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sieteunoseis/netbox-cisco-support/releases/tag/v1.0.0
