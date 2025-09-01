# Generated manually for adding AuditLog
from django.db import migrations, models
import django.db.models.deletion


def create_initial(apps, schema_editor):
    # nothing
    pass

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_create_full_role_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=255)),
                ('target_model', models.CharField(max_length=255)),
                ('target_id', models.CharField(max_length=64)),
                ('before_data', models.JSONField(blank=True, null=True)),
                ('after_data', models.JSONField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_actions', to='core.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.RunPython(create_initial),
    ]
