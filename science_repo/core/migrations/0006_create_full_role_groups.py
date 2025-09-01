from django.db import migrations


def create_role_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for name in [
        "readers",
        "commentators",
        "authors",
        "moderators",
        "review_editors",
        "editorial_office",
        "admins",
    ]:
        Group.objects.get_or_create(name=name)


def delete_role_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=[
        "readers",
        "commentators",
        "authors",
        "moderators",
        "review_editors",
        "editorial_office",
        "admins",
    ]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_create_commentators_group"),
    ]

    operations = [
        migrations.RunPython(create_role_groups, delete_role_groups),
    ]
