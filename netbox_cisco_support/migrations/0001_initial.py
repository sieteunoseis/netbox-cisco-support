from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CiscoSupport",
            fields=[],
            options={
                "managed": False,
                "default_permissions": (),
                "permissions": (("configure_ciscosupport", "Can configure Cisco Support plugin settings"),),
            },
        ),
    ]
