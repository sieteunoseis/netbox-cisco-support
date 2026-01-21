"""
Forms for NetBox Cisco Support Plugin.
"""

from django import forms


class CiscoSupportSettingsForm(forms.Form):
    """Form for displaying plugin settings (read-only)."""

    cisco_client_id = forms.CharField(
        label="Client ID",
        required=False,
        widget=forms.TextInput(attrs={"readonly": True, "class": "form-control"}),
        help_text="Cisco API client ID (configured in configuration.py)",
    )

    cisco_client_secret = forms.CharField(
        label="Client Secret",
        required=False,
        widget=forms.PasswordInput(
            attrs={"readonly": True, "class": "form-control"},
            render_value=True,
        ),
        help_text="Cisco API client secret (masked)",
    )

    manufacturer_pattern = forms.CharField(
        label="Manufacturer Pattern",
        required=False,
        widget=forms.TextInput(attrs={"readonly": True, "class": "form-control"}),
        help_text="Regex pattern to match Cisco manufacturers",
    )

    timeout = forms.IntegerField(
        label="API Timeout",
        required=False,
        widget=forms.NumberInput(attrs={"readonly": True, "class": "form-control"}),
        help_text="API request timeout in seconds",
    )

    cache_timeout = forms.IntegerField(
        label="Cache Timeout",
        required=False,
        widget=forms.NumberInput(attrs={"readonly": True, "class": "form-control"}),
        help_text="Cache duration for API responses in seconds",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mask the client secret
        if self.initial.get("cisco_client_secret"):
            self.initial["cisco_client_secret"] = "********"
