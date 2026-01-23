"""
NetBox Cisco Support Plugin

Displays Cisco product information, bugs, EoX dates, and security advisories
for devices with valid serial numbers from Cisco manufacturer.
"""

from netbox.plugins import PluginConfig

__version__ = "1.0.5"


class CiscoSupportConfig(PluginConfig):
    """Plugin configuration for NetBox Cisco Support."""

    name = "netbox_cisco_support"
    verbose_name = "Cisco Support"
    description = "Display Cisco Support information including product details, EoX dates, bugs, and security advisories"
    version = __version__
    author = "Jeremy Worden"
    author_email = "jeremy.worden@gmail.com"
    base_url = "cisco-support"
    min_version = "4.0.0"
    max_version = "4.99"

    default_settings = {
        "cisco_client_id": "",
        "cisco_client_secret": "",
        "manufacturer_pattern": r"cisco",
        "timeout": 30,
        "cache_timeout": 300,
    }


config = CiscoSupportConfig
