from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings
import os


class Command(BaseCommand):
    help = (
        "Reset the database by dropping all tables and re-applying migrations. "
        "For PostgreSQL, this uses the drop_all_tables command. For SQLite, it removes the DB file."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            action="store_true",
            help="Do not prompt for confirmation.",
        )
        parser.add_argument(
            "--seed",
            action="store_true",
            help="Run seed_data after migrations (if available).",
        )

    def handle(self, *args, **options):
        noinput = options.get("noinput", False)
        do_seed = options.get("seed", False)

        vendor = connection.vendor
        db_name = settings.DATABASES["default"].get("NAME")

        if not noinput:
            confirm = input(
                f"This will IRREVERSIBLY reset the database for backend '{vendor}' (NAME={db_name}).\n"
                f"All tables will be dropped and migrations re-applied.\n"
                f"Type 'yes' to continue: "
            ).strip()
            if confirm.lower() != "yes":
                self.stdout.write(self.style.WARNING("Aborted by user."))
                return

        # Drop all tables depending on backend
        if vendor == "postgresql":
            self.stdout.write(self.style.WARNING("Dropping PostgreSQL schema (via drop_all_tables)..."))
            call_command("drop_all_tables")
        elif vendor == "sqlite":
            self.stdout.write(self.style.WARNING("Detected SQLite backend. Removing database file if it exists..."))
            if db_name and os.path.exists(db_name):
                try:
                    os.remove(db_name)
                    self.stdout.write(self.style.SUCCESS(f"Removed SQLite DB file: {db_name}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Failed to remove SQLite DB file '{db_name}': {e}"))
                    raise
            else:
                self.stdout.write("SQLite DB file not found; proceeding with fresh migrate.")
        else:
            self.stderr.write(self.style.ERROR(f"Unsupported DB backend for automatic reset: {vendor}"))
            return

        # Re-apply all migrations
        self.stdout.write(self.style.WARNING("Applying migrations (manage.py migrate --noinput)..."))
        call_command("migrate", "--noinput")
        self.stdout.write(self.style.SUCCESS("Migrations applied successfully."))

        # Optionally seed data
        if do_seed:
            try:
                self.stdout.write(self.style.WARNING("Seeding initial data (seed_data)..."))
                call_command("seed_data")
                self.stdout.write(self.style.SUCCESS("Seed data applied."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Seeding failed: {e}"))
                # Do not raise by default; seeding is optional

        # Final status
        self.stdout.write(self.style.SUCCESS("Database reset completed."))
