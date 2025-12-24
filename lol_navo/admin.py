from django.contrib import admin

from . import models


@admin.register(models.Champion)
class ChampionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("id", "name", "tags")


@admin.register(models.Summoner)
class SummonerAdmin(admin.ModelAdmin):
    list_display = ("puuid", "username", "server", "ranked_solo_rank")
    search_fields = ("puuid", "username")
    list_filter = ("server", "ranked_solo_rank", "ranked_flex_rank")


@admin.register(models.Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("id", "duration", "winner_team", "gold_diff")
    search_fields = ("id",)


@admin.register(models.MatchSummoners)
class MatchSummonersAdmin(admin.ModelAdmin):
    list_display = ("match", "summoner", "champion", "winner", "kills", "deaths", "assists")
    list_filter = ("winner", "game_type")
    search_fields = ("match__id", "summoner__username", "name")


@admin.register(models.ChampionStat)
class ChampionStatAdmin(admin.ModelAdmin):
    list_display = ("summoner", "champion", "point", "games")
    search_fields = ("summoner__username", "name")


@admin.register(models.Rune)
class RuneAdmin(admin.ModelAdmin):
    list_display = ("id", "rune_name", "rune_value")
    search_fields = ("id", "rune_name")


@admin.register(models.Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "value")
    search_fields = ("id", "name")


@admin.register(models.DataDragonVersion)
class DataDragonVersionAdmin(admin.ModelAdmin):
    """
    Admin interface for Data Dragon version tracking.

    This model tracks when we last synced static data (champions/items/runes)
    and prevents unnecessary syncs when the version hasn't changed.
    """
    list_display = ('version', 'synced_at', 'created_at')
    readonly_fields = ('version', 'synced_at', 'created_at')
    ordering = ['-synced_at']

    def has_add_permission(self, request):
        # Prevent manual creation - only via sync task
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow deletion to force re-sync
        return True
