"""
Navigation menu for NetBox Cisco Support Plugin.
"""

from django.conf import settings
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

_menu = PluginMenu(
    label="Cisco Support",
    groups=(
        (
            "Configuration",
            (
                PluginMenuItem(
                    link="plugins:netbox_cisco_support:settings",
                    link_text="Settings",
                    permissions=["netbox_cisco_support.configure_ciscosupport"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:netbox_cisco_support:test_connection",
                            title="Test Connection",
                            icon_class="mdi mdi-connection",
                        ),
                    ),
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-shield-check",
)


# top_level_menu=False puts this plugin's items under the shared "Plugins" menu
# (grouped by plugin name) instead of its own top-level sidebar menu.
if settings.PLUGINS_CONFIG.get("netbox_cisco_support", {}).get("top_level_menu", True):
    menu = _menu
else:
    menu_items = tuple(item for group in _menu.groups for item in group.items)
