from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    ChampionViewSet,
    SummonerViewSet,
    MatchViewSet,
    ItemViewSet,
    RuneViewSet,
    PatchViewSet,
    ChampionRoleStatsViewSet,
    BuildStatsViewSet,
    MatchupStatsViewSet
)


app_name = "lol_navo"

router = DefaultRouter()

# Core data endpoints
router.register(r'champions', ChampionViewSet, basename="champion")
router.register(r'summoners', SummonerViewSet, basename="summoner")
router.register(r'matches', MatchViewSet, basename="match")
router.register(r'items', ItemViewSet, basename="item")
router.register(r'runes', RuneViewSet, basename="rune")
router.register(r'patches', PatchViewSet, basename="patch")

# Analytics/stats endpoints
router.register(r'champion-stats', ChampionRoleStatsViewSet, basename="champion-stats")
router.register(r'build-stats', BuildStatsViewSet, basename="build-stats")
router.register(r'matchup-stats', MatchupStatsViewSet, basename="matchup-stats")

urlpatterns = router.urls
