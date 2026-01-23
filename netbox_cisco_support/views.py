"""
Views for NetBox Cisco Support Plugin.
"""

import logging
import re

from dcim.models import Device
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.views import View
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
        weight=9100,
        permission="dcim.view_device",
        hide_if_empty=False,
        visible=should_show_cisco_support_tab,
    )

    def get(self, request, pk):
        device = Device.objects.select_related(
            "device_type__manufacturer", "platform"
        ).get(pk=pk)

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
        bugs_version_data = None
        psirt_data = None
        software_data = None
        coverage_data = None
        stack_coverage_data = None
        product_id = None
        software_version = None
        stack_serials = []
        error = None

        # Get software version from custom fields or platform
        software_version = self._get_software_version(device)

        # Parse serial numbers - device.serial may contain comma-separated stack members
        # e.g., "FCW2220G1DM, FCW2221E03P" for a 2-member stack
        all_serials = self._parse_serials(device.serial)
        serial_number = all_serials[0] if all_serials else device.serial
        stack_serials = (
            all_serials[1:] if len(all_serials) > 1 else self._get_stack_serials(device)
        )

        # Step 1: Get product info from serial number
        product_response = client.get_product_info(serial_number)

        if "error" in product_response:
            error = product_response["error"]
        else:
            product_list = product_response.get("product_list", [])
            if product_list:
                product_data = product_list[0]
                product_id = product_data.get("base_pid") or product_data.get(
                    "orderable_pid"
                )
                product_data["cached"] = product_response.get("cached", False)

        # Get device type model as fallback product ID (e.g., "C9300-48P" from device type)
        device_type_model = None
        if device.device_type and device.device_type.model:
            device_type_model = device.device_type.model

        # Step 2: Get EoX info by serial number
        if serial_number and not error:
            eox_response = client.get_eox_by_serial(serial_number)
            if "error" not in eox_response:
                eox_records = eox_response.get("EOXRecord", [])
                if eox_records:
                    eox_data = eox_records[0]
                    eox_data["cached"] = eox_response.get("cached", False)

        # Get cc_series custom field for product_name API (e.g., "Cisco Catalyst 9300 Series Switches")
        cc_series = None
        if hasattr(device, "custom_field_data") and device.custom_field_data:
            cc_series = device.custom_field_data.get("cc_series")

        # Step 3: Get general bugs (NOT version-specific) - by keyword or product_id
        # Note: Severity parameter removed - causes 500 errors on Cisco API
        # We filter client-side instead to get high severity bugs (1-3)
        bug_pid = product_id or device_type_model
        bugs_response = None

        # Approach 1: Keyword search using device type model (most reliable)
        if device_type_model and not error:
            bugs_response = client.get_bugs_by_keyword(device_type_model)

        # Approach 2: Fall back to product_id endpoint
        if (
            (bugs_response is None or "error" in bugs_response)
            and bug_pid
            and not error
        ):
            bugs_response = client.get_bugs_by_product(bug_pid)

        if bugs_response and "error" not in bugs_response:
            # Filter for high severity bugs (1-3) client-side
            all_bugs = bugs_response.get("bugs", [])
            high_severity_bugs = [
                b for b in all_bugs if b.get("severity") in ["1", "2", "3", 1, 2, 3]
            ][:5]
            bugs_data = {
                "bugs": high_severity_bugs if high_severity_bugs else all_bugs[:5],
                "cached": bugs_response.get("cached", False),
            }

        # Step 3b: Get bugs by software version (try product_name first, then keyword)
        # Note: Severity parameter removed - causes 500 errors on Cisco API
        bugs_ver_response = None
        if software_version and not error:
            # Try product_name + affected_releases if cc_series available
            if cc_series:
                bugs_ver_response = client.get_bugs_by_product_name_and_version(
                    cc_series, software_version
                )

            # Fall back to product_id + software_releases if available
            if (bugs_ver_response is None or "error" in bugs_ver_response) and bug_pid:
                bugs_ver_response = client.get_bugs_by_product_and_version(
                    bug_pid, software_version
                )

        if bugs_ver_response and "error" not in bugs_ver_response:
            # Filter for high severity bugs (1-3) client-side
            all_ver_bugs = bugs_ver_response.get("bugs", [])
            high_severity_ver_bugs = [
                b for b in all_ver_bugs if b.get("severity") in ["1", "2", "3", 1, 2, 3]
            ][:5]
            bugs_version_data = {
                "bugs": (
                    high_severity_ver_bugs
                    if high_severity_ver_bugs
                    else all_ver_bugs[:5]
                ),
                "version": software_version,
                "cached": bugs_ver_response.get("cached", False),
            }

        # Step 4: Get PSIRT advisories by product ID
        if product_id and not error:
            psirt_response = client.get_psirt_by_product(product_id)
            if "error" not in psirt_response:
                advisories = psirt_response.get("advisories", [])
                psirt_data = {
                    "advisories": advisories[:10],
                    "total": len(advisories),
                    "cached": psirt_response.get("cached", False),
                }

        # Step 5: Get software suggestions by product ID
        if product_id and not error:
            software_response = client.get_software_suggestions(product_id)
            if "error" not in software_response:
                software_data = software_response
                software_data["cached"] = software_response.get("cached", False)

        # Step 6: Get coverage status by serial number
        if serial_number and not error:
            coverage_response = client.get_coverage_status(serial_number)
            if "error" not in coverage_response:
                serial_numbers_list = coverage_response.get("serial_numbers", [])
                if serial_numbers_list:
                    coverage_data = serial_numbers_list[0]
                    coverage_data["cached"] = coverage_response.get("cached", False)

        # Step 6b: Get stack coverage (if stack serials available)
        if stack_serials and not error:
            # Include primary serial in the list if not already there
            all_serials = [serial_number] + [
                s for s in stack_serials if s != serial_number
            ]
            stack_response = client.get_coverage_summary_bulk(all_serials)
            if "error" not in stack_response:
                stack_serial_list = stack_response.get("serial_numbers", [])
                if stack_serial_list:
                    # Calculate summary stats
                    covered = sum(
                        1 for s in stack_serial_list if s.get("is_covered") == "YES"
                    )
                    not_covered = len(stack_serial_list) - covered
                    stack_coverage_data = {
                        "members": stack_serial_list,
                        "total": len(stack_serial_list),
                        "covered": covered,
                        "not_covered": not_covered,
                        "cached": stack_response.get("cached", False),
                    }

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
                "cc_series": cc_series,
                "software_version": software_version,
                "product_data": product_data,
                "eox_data": eox_data,
                "bugs_data": bugs_data,
                "bugs_version_data": bugs_version_data,
                "psirt_data": psirt_data,
                "software_data": software_data,
                "coverage_data": coverage_data,
                "stack_coverage_data": stack_coverage_data,
            },
        )

    def _parse_serials(self, serial_field):
        """
        Parse serial number field which may contain comma-separated stack members.

        Args:
            serial_field: Device serial field value (e.g., "FCW2220G1DM, FCW2221E03P")

        Returns:
            List of serial numbers, with primary first.
        """
        if not serial_field:
            return []

        # Split by comma and clean up
        serials = [s.strip() for s in serial_field.split(",") if s.strip()]
        return serials

    def _get_software_version(self, device):
        """
        Get software version from device custom fields or platform.

        Checks for:
        1. Custom field 'software_version' or 'sw_version'
        2. Device platform description
        """
        # Check custom fields
        if hasattr(device, "custom_field_data") and device.custom_field_data:
            for field in ["software_version", "sw_version", "ios_version", "version"]:
                if (
                    field in device.custom_field_data
                    and device.custom_field_data[field]
                ):
                    return str(device.custom_field_data[field])

        # Check platform (sometimes includes version info)
        if device.platform and device.platform.name:
            # Try to extract version from platform name if it looks like a version
            match = re.search(r"(\d+\.\d+(?:\.\d+)?)", device.platform.name)
            if match:
                return match.group(1)

        return None

    def _get_stack_serials(self, device):
        """
        Get additional stack member serial numbers from custom fields.

        This is a fallback when device.serial doesn't contain comma-separated values.

        Checks custom fields: 'stack_serials', 'stack_members', 'member_serials'

        Returns list of additional serial numbers.
        """
        if not hasattr(device, "custom_field_data") or not device.custom_field_data:
            return []

        for field in ["stack_serials", "stack_members", "member_serials"]:
            if field in device.custom_field_data and device.custom_field_data[field]:
                value = str(device.custom_field_data[field])
                serials = [s.strip() for s in re.split(r"[,;\s]+", value) if s.strip()]
                return serials

        return []


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
            return JsonResponse(
                {
                    "success": False,
                    "message": "Cisco Support API credentials not configured",
                }
            )

        result = client.test_connection()
        return JsonResponse(result)
