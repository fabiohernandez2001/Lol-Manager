"""
Management command to sync static data from Data Dragon.

Usage:
    python3 manage.py sync_static_data
    python3 manage.py sync_static_data --version=15.21.1
    python3 manage.py sync_static_data --champions-only
    python3 manage.py sync_static_data --items-only
    python3 manage.py sync_static_data --runes-only
"""

from django.core.management.base import BaseCommand
from lol_update.services.static_data_service import (
    sync_champions,
    sync_items,
    sync_runes,
    sync_all_static_data,
    get_latest_version,
)


class Command(BaseCommand):
    help = 'Sync static data (champions, items, runes) from Riot Data Dragon'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patch',
            type=str,
            help='Specific patch version to sync (e.g., 15.21.1). Defaults to latest.',
        )
        parser.add_argument(
            '--champions-only',
            action='store_true',
            help='Sync only champions',
        )
        parser.add_argument(
            '--items-only',
            action='store_true',
            help='Sync only items',
        )
        parser.add_argument(
            '--runes-only',
            action='store_true',
            help='Sync only runes',
        )

    def handle(self, *args, **options):
        version = options.get('patch')
        champions_only = options.get('champions_only')
        items_only = options.get('items_only')
        runes_only = options.get('runes_only')

        # Get version
        if not version:
            self.stdout.write("Fetching latest version...")
            version = get_latest_version()
            if not version:
                self.stdout.write(self.style.ERROR("Failed to fetch latest version"))
                return

        self.stdout.write(self.style.SUCCESS(f"Using version: {version}"))

        # Sync based on flags
        if champions_only:
            self.stdout.write("Syncing champions...")
            created, updated = sync_champions(version)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Champions synced: {created} created, {updated} updated"
                )
            )

        elif items_only:
            self.stdout.write("Syncing items...")
            created, updated = sync_items(version)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Items synced: {created} created, {updated} updated"
                )
            )

        elif runes_only:
            self.stdout.write("Syncing runes...")
            created, updated = sync_runes(version)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Runes synced: {created} created, {updated} updated"
                )
            )

        else:
            # Sync all
            self.stdout.write("Syncing all static data (champions, items, runes)...")
            results = sync_all_static_data(version)

            self.stdout.write(self.style.SUCCESS("\nSync complete:"))
            for data_type, (created, updated) in results.items():
                self.stdout.write(
                    f"  {data_type.capitalize()}: {created} created, {updated} updated"
                )

        self.stdout.write(self.style.SUCCESS("\n✓ Static data sync complete!"))
