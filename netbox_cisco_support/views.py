"""
Views for NetBox Cisco Support Plugin.
"""

import logging
import re

from django.conf import settings
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from dcim.models import Device
from netbox.views.generic import ObjectView
from utilities.views import ViewTab, register_model_view

from .cisco_client import get_client
from .forms import CiscoSupportSettingsForm

logger = logging.getLogger(__name__)


def should_show_cisco_support_tab(device):
    """
    Determine if the Cisco Support tab should be shown for a device.

    Requirements:
    1. Device must have a serial number
    2. Device must have a manufacturer matching the configured pattern (default: 'cisco')
    """
    config = settings.PLUGINS_CONFIG.get("netbox_cisco_support", {})
    pattern = config.get("manufacturer_pattern", r"cisco")

    # Must have a serial number
    if not device.serial:
        return False

    # Must have manufacturer matching pattern
    if not device.device_type or not device.device_type.manufacturer:
        return False

    manufacturer_name = device.device_type.manufacturer.name
    return bool(re.search(pattern, manufacturer_name, re.IGNORECASE))


@register_model_view(Device, "cisco_support", path="cisco-support")
class DeviceCiscoSupportView(ObjectView):
    """Display Cisco Support information for a device."""

    queryset = Device.objects.all()
    template_name = "netbox_cisco_support/device_tab.html"
    tab = ViewTab(
        label="Cisco Support",
        badge=lambda obj: "EoX" if should_show_cisco_support_tab(obj) else None,
        permission="dcim.view_device",
        hide_if_empty=True,
    )

    def get(self, request, pk):
        device = self.get_object()

        # Check if tab should be shown
        if not should_show_cisco_support_tab(device):
            return render(
                request,
                self.template_name,
                {
                    "object": device,
                    "tab": self.tab,
                    "show_tab": False,
                    "error": "Device does not meet requirements for Cisco Support lookup",
                },
            )

        # Get Cisco client
        client = get_client()
        if not client:
            return render(
                request,
                self.template_name,
                {
                    "object": device,
                    "tab": self.tab,
                    "show_tab": True,
                    "error": "Cisco Support API credentials not configured",
                },
            )

        # Initialize data containers
        product_data = None
        eox_data = None
        bugs_data = None
        psirt_data = None
        software_data = None
        product_id = None
        error = None

        # Step 1: Get product info from serial number
        serial_number = device.serial
        product_response = client.get_product_info(serial_number)

        if "error" in product_response:
            error = product_response["error"]
        else:
            product_list = product_response.get("product_list", [])
            if product_list:
                product_data = product_list[0]
                product_id = product_data.get("base_pid") or product_data.get("orderable_pid")
                product_data["cached"] = product_response.get("cached", False)

        # Step 2: Get EoX info by serial number
        if serial_number and not error:
            eox_response = client.get_eox_by_serial(serial_number)
            if "error" not in eox_response:
                eox_records = eox_response.get("EOXRecord", [])
                if eox_records:
                    eox_data = eox_records[0]
                    eox_data["cached"] = eox_response.get("cached", False)

        # Step 3: Get bugs by product ID
        if product_id and not error:
            bugs_response = client.get_bugs_by_product(product_id, severity="1,2,3")
            if "error" not in bugs_response:
                bugs_data = bugs_response.get("bugs", [])[:10]  # Top 10 bugs
                bugs_data = {
                    "bugs": bugs_data,
                    "cached": bugs_response.get("cached", False),
                }

        # Step 4: Get PSIRT advisories by product ID
        if product_id and not error:
            psirt_response = client.get_psirt_by_product(product_id)
            if "error" not in psirt_response:
                advisories = psirt_response.get("advisories", [])
                psirt_data = {
                    "advisories": advisories[:10],  # Top 10 advisories
                    "total": len(advisories),
                    "cached": psirt_response.get("cached", False),
                }

        # Step 5: Get software suggestions by product ID
        if product_id and not error:
            software_response = client.get_software_suggestions(product_id)
            if "error" not in software_response:
                software_data = software_response
                software_data["cached"] = software_response.get("cached", False)

        return render(
            request,
            self.template_name,
            {
                "object": device,
                "tab": self.tab,
                "show_tab": True,
                "error": error,
                "serial_number": serial_number,
                "product_id": product_id,
                "product_data": product_data,
                "eox_data": eox_data,
                "bugs_data": bugs_data,
                "psirt_data": psirt_data,
                "software_data": software_data,
            },
        )


class CiscoSupportSettingsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Plugin settings view."""

    permission_required = "dcim.view_device"
    template_name = "netbox_cisco_support/settings.html"

    def get(self, request):
        config = settings.PLUGINS_CONFIG.get("netbox_cisco_support", {})
        form = CiscoSupportSettingsForm(initial=config)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "config": config,
            },
        )


class TestConnectionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Test Cisco API connection."""

    permission_required = "dcim.view_device"

    def get(self, request):
        from django.http import JsonResponse

        client = get_client()
        if not client:
            return JsonResponse({
                "success": False,
                "message": "Cisco Support API credentials not configured",
            })

        result = client.test_connection()
        return JsonResponse(result)
