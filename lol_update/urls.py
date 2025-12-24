from django.urls import path
from . import views


app_name = "lol_update"

urlpatterns = [
    # New REST API endpoints for service triggers
    path("api/fetch-summoner/", views.FetchSummonerView.as_view(), name="fetch-summoner"),
    path("api/fetch-matches/", views.FetchMatchesView.as_view(), name="fetch-matches"),
    path("api/sync-static-data/", views.SyncStaticDataView.as_view(), name="sync-static-data"),
    path("api/update-rank/", views.UpdateSummonerRankView.as_view(), name="update-rank"),

    # Legacy endpoints (kept for backward compatibility)
    path("champions", views.get_champions, name="champions"),
    path("items", views.get_items, name="items"),
]