from django.db import models


class CiscoSupport(models.Model):
    """Unmanaged model to register custom permissions for the Cisco Support plugin."""

    # Excluded from NetBox's /core/system/ object-count loop; the model has no DB table.
    _netbox_private = True

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (("configure_ciscosupport", "Can configure Cisco Support plugin settings"),)
