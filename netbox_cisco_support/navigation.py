"""
Navigation menu for NetBox Cisco Support Plugin.
"""

from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

menu = PluginMenu(
    label="Cisco Support",
    groups=(
        (
            "Configuration",
            (
                PluginMenuItem(
                    link="plugins:netbox_cisco_support:settings",
                    link_text="Settings",
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
