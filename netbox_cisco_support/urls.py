"""
URL patterns for NetBox Cisco Support Plugin.
"""

from django.urls import path

from .views import (
    CiscoSupportSettingsView,
    DeviceCiscoSupportContentView,
    TestConnectionView,
)

urlpatterns = [
    path("settings/", CiscoSupportSettingsView.as_view(), name="settings"),
    path("test-connection/", TestConnectionView.as_view(), name="test_connection"),
    path(
        "device/<int:pk>/content/",
        DeviceCiscoSupportContentView.as_view(),
        name="device_content",
    ),
]
