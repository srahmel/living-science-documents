from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0003_populate_comment_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='range_hash',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='commentmoderation',
            name='checked_question_form',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='commentmoderation',
            name='checked_sources',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='commentmoderation',
            name='checked_anchor',
            field=models.BooleanField(default=False),
        ),
    ]
