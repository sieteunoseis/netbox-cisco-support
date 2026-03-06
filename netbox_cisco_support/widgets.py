"""Dashboard widgets for the NetBox Cisco Support plugin."""

import logging
from datetime import date, datetime

from django import forms
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from extras.dashboard.utils import register_widget
from extras.dashboard.widgets import DashboardWidget, WidgetConfigForm

from .cisco_client import get_client

logger = logging.getLogger(__name__)


@register_widget
class CiscoLifecycleWidget(DashboardWidget):
    """Dashboard widget showing EoX/PSIRT lifecycle summary across devices."""

    default_title = _("Cisco Lifecycle")
    description = _("Display EoX and PSIRT advisory summary for Cisco devices.")
    template_name = "netbox_cisco_support/widgets/lifecycle_summary.html"
    width = 4
    height = 3

    class ConfigForm(WidgetConfigForm):
        cache_timeout = forms.IntegerField(
            min_value=300,
            max_value=86400,
            initial=3600,
            required=False,
            label=_("Cache timeout (seconds)"),
            help_text=_("How long to cache lifecycle data (300-86400 seconds). Cisco data changes infrequently."),
        )

    def render(self, request):
        client = get_client()
        if not client:
            return render_to_string(
                self.template_name,
                {
                    "error": "Cisco Support API not configured. Set cisco_client_id and cisco_client_secret in plugin settings."
                },
            )

        cache_timeout = self.config.get("cache_timeout", 3600)
        summary = client.get_lifecycle_summary(cache_timeout=cache_timeout)

        if "error" in summary:
            return render_to_string(self.template_name, {"error": summary["error"]})

        return render_to_string(
            self.template_name,
            {
                "eox": summary.get("eox", {}),
                "psirt": summary.get("psirt", {}),
                "total_devices": summary.get("total_devices", 0),
                "cached": summary.get("cached", False),
            },
        )
