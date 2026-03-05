from django.db import models


class CiscoSupport(models.Model):
    """Unmanaged model to register custom permissions for the Cisco Support plugin."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("configure_ciscosupport", "Can configure Cisco Support plugin settings"),
        )
