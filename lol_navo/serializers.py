from rest_framework import serializers
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


class ChampionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Champion
        fields = "__all__"


class SummonerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Summoner
        fields = "__all__"


class PatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patch
        fields = "__all__"


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class RuneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rune
        fields = "__all__"


class MatchSummonersSerializer(serializers.ModelSerializer):
    """Serializer for match participant data."""
    summoner_username = serializers.CharField(source='summoner.username', read_only=True)
    summoner_tag = serializers.CharField(source='summoner.tag', read_only=True)
    champion_name = serializers.CharField(source='champion.name', read_only=True)
    champion_icon = serializers.URLField(source='champion.icon', read_only=True)

    class Meta:
        model = MatchSummoners
        fields = "__all__"


class MatchSerializer(serializers.ModelSerializer):
    """Serializer for match data."""
    participants = MatchSummonersSerializer(source='match_entries', many=True, read_only=True)
    patch_version_display = serializers.CharField(source='patch_version.version', read_only=True)

    class Meta:
        model = Match
        fields = "__all__"


class MatchListSerializer(serializers.ModelSerializer):
    """Lighter serializer for match lists (without full participant data)."""
    patch_version_display = serializers.CharField(source='patch_version.version', read_only=True)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Match
        exclude = ['raw_data']  # Exclude raw JSON from list view

    def get_participant_count(self, obj):
        return obj.match_entries.count()


class ChampionStatSerializer(serializers.ModelSerializer):
    """Serializer for summoner champion stats."""
    summoner_username = serializers.CharField(source='summoner.username', read_only=True)
    champion_name = serializers.CharField(source='champion.name', read_only=True)
    champion_icon = serializers.URLField(source='champion.icon', read_only=True)
    patch_display = serializers.CharField(source='patch_version.version', read_only=True)

    class Meta:
        model = ChampionStat
        fields = "__all__"


class ChampionRoleStatsSerializer(serializers.ModelSerializer):
    """Serializer for champion performance by role and patch."""
    champion_name = serializers.CharField(source='champion.name', read_only=True)
    champion_icon = serializers.URLField(source='champion.icon', read_only=True)
    patch_display = serializers.CharField(source='patch.version', read_only=True)

    class Meta:
        model = ChampionRoleStats
        fields = "__all__"


class BuildStatsSerializer(serializers.ModelSerializer):
    """Serializer for item build statistics."""
    champion_name = serializers.CharField(source='champion.name', read_only=True)
    champion_icon = serializers.URLField(source='champion.icon', read_only=True)
    patch_display = serializers.CharField(source='patch.version', read_only=True)

    class Meta:
        model = BuildStats
        fields = "__all__"


class MatchupStatsSerializer(serializers.ModelSerializer):
    """Serializer for champion matchup statistics."""
    champion_name = serializers.CharField(source='champion.name', read_only=True)
    opponent_name = serializers.CharField(source='opponent.name', read_only=True)
    champion_icon = serializers.URLField(source='champion.icon', read_only=True)
    opponent_icon = serializers.URLField(source='opponent.icon', read_only=True)
    patch_display = serializers.CharField(source='patch.version', read_only=True)

    class Meta:
        model = MatchupStats
        fields = "__all__"