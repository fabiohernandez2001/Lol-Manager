"""
Management command to fetch match history for a summoner.

Usage:
    python3 manage.py fetch_matches <puuid> --count=20 --region=euw
    python3 manage.py fetch_matches <puuid> --count=50 --region=na --queue=ranked
"""

from django.core.management.base import BaseCommand, CommandError
from lol_update.services.match_service import bulk_fetch_matches
from lol_update.services.summoner_service import get_summoner_by_puuid


class Command(BaseCommand):
    help = 'Fetch match history for a summoner by PUUID'

    def add_arguments(self, parser):
        parser.add_argument(
            'puuid',
            type=str,
            help='Summoner PUUID',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of matches to fetch (max 100). Default: 20',
        )
        parser.add_argument(
            '--region',
            type=str,
            default='euw',
            help='Platform region (e.g., euw, na, kr). Default: euw',
        )
        parser.add_argument(
            '--queue',
            type=str,
            help='Queue type filter (e.g., ranked, normal). Optional.',
        )

    def handle(self, *args, **options):
        puuid = options['puuid']
        count = min(options['count'], 100)  # API limit
        region = options['region']
        queue_type = options.get('queue')

        # Check if summoner exists in database
        summoner = get_summoner_by_puuid(puuid)
        if summoner:
            self.stdout.write(
                f"Fetching {count} matches for {summoner.username}..."
            )
        else:
            self.stdout.write(
                f"Fetching {count} matches for PUUID {puuid[:8]}... "
                "(summoner not in database)"
            )

        # Fetch matches
        matches = bulk_fetch_matches(
            puuid=puuid,
            region=region,
            count=count,
            queue_type=queue_type
        )

        if matches:
            self.stdout.write(
                self.style.SUCCESS(f"\n✓ Fetched {len(matches)} matches successfully!")
            )

            # Show summary
            self.stdout.write("\nMatch Summary:")
            for i, match in enumerate(matches[:5], 1):  # Show first 5
                self.stdout.write(
                    f"  {i}. {match.id} - "
                    f"Queue {match.queue_type} - "
                    f"{match.duration} - "
                    f"Winner: Team {match.winner_team}"
                )

            if len(matches) > 5:
                self.stdout.write(f"  ... and {len(matches) - 5} more")

        else:
            raise CommandError(
                f"Failed to fetch matches for PUUID {puuid}. "
                "Check logs for details."
            )
