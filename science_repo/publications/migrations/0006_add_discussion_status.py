from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0005_documentversion_html_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentversion',
            name='discussion_status',
            field=models.CharField(choices=[('open', 'Open'), ('closed', 'Closed'), ('withdrawn', 'Withdrawn')], default='open', max_length=20),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='discussion_closed_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='discussion_closed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='closed_discussions', to='auth.user'),
        ),
    ]