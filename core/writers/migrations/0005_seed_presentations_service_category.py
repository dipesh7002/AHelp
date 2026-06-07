from django.db import migrations


def seed_presentations_category(apps, schema_editor):
    Service = apps.get_model("writers", "Service")
    ServiceCategory = apps.get_model("writers", "ServiceCategory")

    category, _ = ServiceCategory.objects.get_or_create(
        name="Presentations",
        defaults={"sort_order": 5},
    )
    Service.objects.filter(name="Presentation Slides").update(category=category)


def unassign_presentations_category(apps, schema_editor):
    Service = apps.get_model("writers", "Service")
    Service.objects.filter(name="Presentation Slides").update(category=None)


class Migration(migrations.Migration):

    dependencies = [
        ("writers", "0004_servicecategory_alter_service_options_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_presentations_category, unassign_presentations_category),
    ]
