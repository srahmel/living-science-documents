# Generated manually: add doi_status to DocumentVersion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0009_add_created_at_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentversion',
            name='doi_status',
            field=models.CharField(choices=[('draft', 'Draft'), ('registered', 'Registered'), ('findable', 'Findable'), ('error', 'Error')], default='draft', max_length=20),
        ),
    ]
