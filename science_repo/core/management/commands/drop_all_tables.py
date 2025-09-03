from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.utils import ProgrammingError


class Command(BaseCommand):
    help = "Drop all database tables for the current connection (PostgreSQL only). USE WITH CAUTION."

    def handle(self, *args, **options):
        vendor = connection.vendor
        if vendor != 'postgresql':
            self.stderr.write(self.style.ERROR(
                f"This command currently supports only PostgreSQL. Detected backend: {vendor}"
            ))
            return

        with connection.cursor() as cursor:
            self.stdout.write(self.style.WARNING("Dropping all tables (CASCADE) in current schema..."))
            try:
                # Drop and recreate public schema to remove all tables, sequences, constraints, etc.
                cursor.execute("DROP SCHEMA public CASCADE;")
                cursor.execute("CREATE SCHEMA public;")
                # Restore default privileges for public schema
                cursor.execute("GRANT ALL ON SCHEMA public TO public;")
            except ProgrammingError as e:
                self.stderr.write(self.style.ERROR(f"Error while dropping/recreating schema: {e}"))
                raise

        # Ensure the transaction is committed (autocommit is default, but be explicit)
        try:
            transaction.commit()
        except Exception:
            # In autocommit mode this may do nothing
            pass

        self.stdout.write(self.style.SUCCESS("All tables dropped. You can now run 'python manage.py migrate' to recreate schema."))
