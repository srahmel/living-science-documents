from django.db import migrations
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Placeholder initial migration created during squash to satisfy
        # cross-app dependencies (e.g., ai_assistant depends on publications.0001_initial).
        # A follow-up migration will create the actual schema from models.py.
    ]
