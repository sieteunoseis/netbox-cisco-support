# NetBox Cisco Support Plugin

<img src="https://raw.githubusercontent.com/sieteunoseis/netbox-cisco-support/main/docs/icon.png" alt="NetBox Cisco Support Plugin" width="100" align="right">

![NetBox Version](https://img.shields.io/badge/NetBox-4.0+-blue)
![Python Version](https://img.shields.io/badge/Python-3.10+-green)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/sieteunoseis/netbox-cisco-support/actions/workflows/ci.yml/badge.svg)](https://github.com/sieteunoseis/netbox-cisco-support/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/netbox-cisco-support-api)](https://pypi.org/project/netbox-cisco-support-api/)

A NetBox plugin that displays Cisco Support information for devices, including:
- **Product Information** - Product name, series, category, and orderable status
- **End-of-Life (EoX)** - Key lifecycle dates with migration recommendations
- **Security Advisories (PSIRT)** - Cisco security advisories affecting the product
- **Known Bugs** - Critical bugs (severity 1-3) from Cisco Bug Search
- **Software Recommendations** - Suggested software releases

## Features

- **Serial Number Based** - Tab only appears on devices with a valid serial number
- **Manufacturer Filtering** - Configurable pattern to match Cisco manufacturers
- **Direct Cisco API Integration** - Uses Cisco Support APIs with OAuth2 authentication
- **Caching** - API responses are cached to reduce load and improve performance
- **Visual Status Indicators** - Color-coded badges for EoX dates and advisory severity

## Requirements

- NetBox 4.0.0 or higher
- Python 3.10 or higher
- Cisco API credentials (from [Cisco API Console](https://apidocs-prod.cisco.com/))

## Installation

### Via pip (recommended)

```bash
pip install netbox-cisco-support-api
```

### From source

```bash
git clone https://github.com/sieteunoseis/netbox-cisco-support.git
cd netbox-cisco-support
pip install .
```

## Configuration

Add the plugin to your NetBox `configuration.py`:

```python
PLUGINS = [
    'netbox_cisco_support',
]

PLUGINS_CONFIG = {
    'netbox_cisco_support': {
        # Required: Cisco API credentials
        'cisco_client_id': 'your-client-id',
        'cisco_client_secret': 'your-client-secret',

        # Optional: Manufacturer matching pattern (regex, case-insensitive)
        # Default: r'cisco'
        'manufacturer_pattern': r'cisco',

        # Optional: API request timeout in seconds
        'timeout': 30,

        # Optional: Cache duration for API responses in seconds
        'cache_timeout': 300,
    }
}
```

Restart NetBox after making configuration changes.

## Getting Cisco API Credentials

1. Go to [Cisco API Console](https://apiconsole.cisco.com/)
2. Sign in with your Cisco CCO ID
3. Create a new application (or use an existing one)
4. Add the following APIs to your application:

| API Name | Purpose | Required |
|----------|---------|----------|
| **Serial Number to Information (SN2Info) v2** | Coverage status, warranty dates | Yes |
| **Product Information API** | Product name, series, orderable status | Yes |
| **End of Life (EoX) API** | End-of-Life/Sale dates, migration info | Yes |
| **Bug API v2** | Known bugs by product/software version | Recommended |
| **PSIRT API** | Security advisories | Recommended |
| **Software Suggestion API** | Recommended software versions | Optional |

5. Copy your **Client ID** and **Client Secret**

### API Endpoints Used

The plugin calls these specific endpoints:

```
# Coverage/Warranty
GET /sn2info/v2/coverage/status/serial_numbers/{serial}
GET /sn2info/v2/coverage/summary/serial_numbers/{serials}

# Product Information
GET /product/v1/information/serial_numbers/{serial}

# End of Life
GET /supporttools/eox/rest/5/EOXBySerialNumber/1/{serial}

# Bugs
GET /bug/v3.0/bugs/products/product_id/{pid}
GET /bug/v3.0/bugs/software_version/{version}

# Security Advisories
GET /security/advisories/v2/product

# Software Suggestions
GET /software/v4.0/suggestions/releases/productIds/{pid}
```

All APIs use OAuth2 client credentials flow with the same client_id/client_secret.

## Usage

Once configured, the "Cisco Support" tab will automatically appear on device detail pages that meet these requirements:

1. Device has a **serial number** assigned
2. Device manufacturer matches the `manufacturer_pattern` (default: "cisco")

The tab displays:
- Product information from the serial number lookup
- End-of-Life status with key dates
- Security advisories affecting the product
- Known bugs (severity 1-3)
- Software recommendations

## Screenshots

### Device Cisco Support Tab
![Cisco Support Device Tab](https://raw.githubusercontent.com/sieteunoseis/netbox-cisco-support/main/docs/screenshot-device.png)

## Development

### Setup

```bash
git clone https://github.com/sieteunoseis/netbox-cisco-support.git
cd netbox-cisco-support
pip install -e .
```

### Code Quality

```bash
# Format code
black netbox_cisco_support/
isort netbox_cisco_support/

# Lint
flake8 netbox_cisco_support/
```

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Author

Jeremy Worden ([@sieteunoseis](https://github.com/sieteunoseis))

## Links

- [GitHub Repository](https://github.com/sieteunoseis/netbox-cisco-support)
- [PyPI Package](https://pypi.org/project/netbox-cisco-support/)
- [Cisco Support APIs](https://developer.cisco.com/docs/support-apis/)
