"""
Management command to fetch summoner data from Riot API.

Usage:
    python3 manage.py fetch_summoner koldi doggy --region=euw
    python3 manage.py fetch_summoner "Hide on bush" KR1 --region=kr
"""

from django.core.management.base import BaseCommand, CommandError
from lol_update.services.summoner_service import fetch_summoner_by_riot_id


class Command(BaseCommand):
    help = 'Fetch summoner data by Riot ID (game name + tag line)'

    def add_arguments(self, parser):
        parser.add_argument(
            'game_name',
            type=str,
            help='Summoner game name (e.g., "koldi")',
        )
        parser.add_argument(
            'tag_line',
            type=str,
            help='Summoner tag line (e.g., "doggy")',
        )
        parser.add_argument(
            '--region',
            type=str,
            default='euw',
            help='Platform region (e.g., euw, na, kr). Default: euw',
        )

    def handle(self, *args, **options):
        game_name = options['game_name']
        tag_line = options['tag_line']
        region = options['region']

        self.stdout.write(
            f"Fetching summoner: {game_name}#{tag_line} from region {region.upper()}..."
        )

        summoner = fetch_summoner_by_riot_id(
            game_name=game_name,
            tag_line=tag_line,
            region=region
        )

        if summoner:
            self.stdout.write(self.style.SUCCESS("\n✓ Summoner fetched successfully!"))
            self.stdout.write(f"\nSummoner Details:")
            self.stdout.write(f"  Name: {summoner.username}#{tag_line}")
            self.stdout.write(f"  PUUID: {summoner.puuid}")
            self.stdout.write(f"  Server: {summoner.server}")
            self.stdout.write(f"  Solo/Duo: {summoner.ranked_solo_rank} - {summoner.ranked_solo_wins}W / {summoner.ranked_solo_loses}L")
            self.stdout.write(f"  Flex: {summoner.ranked_flex_rank} - {summoner.ranked_flex_wins}W / {summoner.ranked_flex_loses}L")

        else:
            raise CommandError(
                f"Failed to fetch summoner {game_name}#{tag_line}. "
                "Check logs for details."
            )
