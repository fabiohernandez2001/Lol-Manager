from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    Champion,
    Summoner,
    Match,
    MatchSummoners,
    Item,
    Rune,
    Patch,
    ChampionStat,
    ChampionRoleStats,
    BuildStats,
    MatchupStats
)
from .serializers import (
    ChampionSerializer,
    SummonerSerializer,
    MatchSerializer,
    MatchListSerializer,
    MatchSummonersSerializer,
    ItemSerializer,
    RuneSerializer,
    PatchSerializer,
    ChampionStatSerializer,
    ChampionRoleStatsSerializer,
    BuildStatsSerializer,
    MatchupStatsSerializer
)


class ChampionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Champion data.

    Endpoints:
    - GET /champions/ - List all champions
    - GET /champions/{id}/ - Retrieve specific champion
    - GET /champions/?name=Ahri - Filter by name (case-insensitive)
    """
    queryset = Champion.objects.all().order_by("name")
    serializer_class = ChampionSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'title', 'tags']
    ordering_fields = ['name', 'attack', 'defense', 'magic', 'difficulty']

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class SummonerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Summoner data.

    Endpoints:
    - GET /summoners/ - List all summoners
    - GET /summoners/{puuid}/ - Retrieve specific summoner
    - GET /summoners/?username=Faker - Filter by username
    - GET /summoners/?server=na1 - Filter by server
    - GET /summoners/{puuid}/matches/ - Get summoner's matches
    - GET /summoners/{puuid}/champion_stats/ - Get summoner's champion stats
    """
    queryset = Summoner.objects.all().order_by("-ranked_solo_wins")
    serializer_class = SummonerSerializer
    lookup_field = 'puuid'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'tag', 'server']
    ordering_fields = ['username', 'ranked_solo_wins', 'ranked_flex_wins']

    def get_queryset(self):
        queryset = super().get_queryset()
        username = self.request.query_params.get("username")
        server = self.request.query_params.get("server")
        tag = self.request.query_params.get("tag")

        if username:
            queryset = queryset.filter(username__icontains=username)
        if server:
            queryset = queryset.filter(server__iexact=server)
        if tag:
            queryset = queryset.filter(tag__iexact=tag)

        return queryset

    @action(detail=True, methods=['get'])
    def matches(self, request, puuid=None):
        """Get all matches for a specific summoner."""
        summoner = self.get_object()
        matches = Match.objects.filter(summoners=summoner).order_by('-match_timestamp')

        # Apply pagination
        page = self.paginate_queryset(matches)
        if page is not None:
            serializer = MatchListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MatchListSerializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def champion_stats(self, request, puuid=None):
        """Get champion performance stats for a specific summoner."""
        summoner = self.get_object()
        stats = ChampionStat.objects.filter(summoner=summoner).select_related('champion', 'patch_version')
        serializer = ChampionStatSerializer(stats, many=True)
        return Response(serializer.data)


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Match data.

    Endpoints:
    - GET /matches/ - List all matches
    - GET /matches/{match_id}/ - Retrieve specific match with full participant data
    - GET /matches/?region=na1 - Filter by region
    - GET /matches/?queue_type=420 - Filter by queue type (420=Ranked Solo)
    """
    queryset = Match.objects.all().order_by('-match_timestamp').select_related('patch_version')
    lookup_field = 'id'
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['match_timestamp', 'duration', 'queue_type']

    def get_serializer_class(self):
        """Use lighter serializer for list view."""
        if self.action == 'list':
            return MatchListSerializer
        return MatchSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        region = self.request.query_params.get("region")
        queue_type = self.request.query_params.get("queue_type")
        summoner_puuid = self.request.query_params.get("summoner")

        if region:
            queryset = queryset.filter(region__iexact=region)
        if queue_type:
            queryset = queryset.filter(queue_type=queue_type)
        if summoner_puuid:
            queryset = queryset.filter(summoners__puuid=summoner_puuid)

        return queryset


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Item data.

    Endpoints:
    - GET /items/ - List all items
    - GET /items/{id}/ - Retrieve specific item
    - GET /items/?name=Trinity - Filter by name
    """
    queryset = Item.objects.all().order_by("name")
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'plaintext', 'colloq']
    ordering_fields = ['name', 'total_gold', 'base_gold']

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")
        purchasable_only = self.request.query_params.get("purchasable")

        if name:
            queryset = queryset.filter(name__icontains=name)
        if purchasable_only and purchasable_only.lower() == 'true':
            queryset = queryset.filter(purchasable=True)

        return queryset


class RuneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Rune data.

    Endpoints:
    - GET /runes/ - List all runes
    - GET /runes/{id}/ - Retrieve specific rune
    """
    queryset = Rune.objects.all().order_by("rune_name")
    serializer_class = RuneSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['rune_name', 'rune_description']


class PatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Patch data.

    Endpoints:
    - GET /patches/ - List all patches
    - GET /patches/{version}/ - Retrieve specific patch
    - GET /patches/?is_active=true - Filter by active patches
    """
    queryset = Patch.objects.all().order_by("-release_date")
    serializer_class = PatchSerializer
    lookup_field = 'version'

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")

        if is_active and is_active.lower() == 'true':
            queryset = queryset.filter(is_active=True)

        return queryset


class ChampionRoleStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Champion Role Statistics (meta analysis).

    Endpoints:
    - GET /champion-stats/ - List champion stats by role and patch
    - GET /champion-stats/{id}/ - Retrieve specific stat entry
    - GET /champion-stats/?champion={champion_id} - Filter by champion
    - GET /champion-stats/?role=MIDDLE - Filter by role
    - GET /champion-stats/?patch={version} - Filter by patch
    - GET /champion-stats/?queue_type=420 - Filter by queue type
    """
    queryset = ChampionRoleStats.objects.all().select_related('champion', 'patch').order_by('-winrate')
    serializer_class = ChampionRoleStatsSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['winrate', 'pickrate', 'banrate', 'games_played', 'avg_kda']

    def get_queryset(self):
        queryset = super().get_queryset()
        champion_id = self.request.query_params.get("champion")
        role = self.request.query_params.get("role")
        patch = self.request.query_params.get("patch")
        queue_type = self.request.query_params.get("queue_type")
        min_games = self.request.query_params.get("min_games")

        if champion_id:
            queryset = queryset.filter(champion_id=champion_id)
        if role:
            queryset = queryset.filter(role__iexact=role)
        if patch:
            queryset = queryset.filter(patch__version=patch)
        if queue_type:
            queryset = queryset.filter(queue_type=queue_type)
        if min_games:
            queryset = queryset.filter(games_played__gte=int(min_games))

        return queryset


class BuildStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Item Build Statistics.

    Endpoints:
    - GET /build-stats/ - List build stats
    - GET /build-stats/{id}/ - Retrieve specific build stat entry
    - GET /build-stats/?champion={champion_id} - Filter by champion
    - GET /build-stats/?role=MIDDLE - Filter by role
    - GET /build-stats/?patch={version} - Filter by patch
    - GET /build-stats/?build_type=CORE - Filter by build type
    """
    queryset = BuildStats.objects.all().select_related('champion', 'patch').order_by('-winrate')
    serializer_class = BuildStatsSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['winrate', 'games_played']

    def get_queryset(self):
        queryset = super().get_queryset()
        champion_id = self.request.query_params.get("champion")
        role = self.request.query_params.get("role")
        patch = self.request.query_params.get("patch")
        build_type = self.request.query_params.get("build_type")
        min_games = self.request.query_params.get("min_games")

        if champion_id:
            queryset = queryset.filter(champion_id=champion_id)
        if role:
            queryset = queryset.filter(role__iexact=role)
        if patch:
            queryset = queryset.filter(patch__version=patch)
        if build_type:
            queryset = queryset.filter(build_type__iexact=build_type)
        if min_games:
            queryset = queryset.filter(games_played__gte=int(min_games))

        return queryset


class MatchupStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Champion Matchup Statistics.

    Endpoints:
    - GET /matchup-stats/ - List matchup stats
    - GET /matchup-stats/{id}/ - Retrieve specific matchup stat entry
    - GET /matchup-stats/?champion={champion_id} - Filter by champion
    - GET /matchup-stats/?opponent={champion_id} - Filter by opponent
    - GET /matchup-stats/?role=MIDDLE - Filter by role
    - GET /matchup-stats/?patch={version} - Filter by patch
    """
    queryset = MatchupStats.objects.all().select_related('champion', 'opponent', 'patch').order_by('-winrate_delta')
    serializer_class = MatchupStatsSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['winrate', 'winrate_delta', 'games_played']

    def get_queryset(self):
        queryset = super().get_queryset()
        champion_id = self.request.query_params.get("champion")
        opponent_id = self.request.query_params.get("opponent")
        role = self.request.query_params.get("role")
        patch = self.request.query_params.get("patch")
        queue_type = self.request.query_params.get("queue_type")
        min_games = self.request.query_params.get("min_games")

        if champion_id:
            queryset = queryset.filter(champion_id=champion_id)
        if opponent_id:
            queryset = queryset.filter(opponent_id=opponent_id)
        if role:
            queryset = queryset.filter(role__iexact=role)
        if patch:
            queryset = queryset.filter(patch__version=patch)
        if queue_type:
            queryset = queryset.filter(queue_type=queue_type)
        if min_games:
            queryset = queryset.filter(games_played__gte=int(min_games))

        return queryset
