from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Champion, Summoner
from .serializers import ChampionSerializer, SummonerSerializer

class ChampionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Champion.objects.all().order_by("name")
    serializer_class = ChampionSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Champion.objects.all().order_by("name")
        name = self.request.query_params.get("name")  # obtiene ?name=Ahri
        if name:
            queryset = queryset.filter(name__icontains=name)  # busca coincidencias parciales
        return queryset
    
    def list(self,request):
        champions = Champion.objects.all()
        serializer = ChampionSerializer(champions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def get_name(self, request):
        champions = self.queryset.filter(name__icontains=request.query_params.get("name"))
        serializer = ChampionSerializer(champions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def get_summoner(self, request):
        name = request.query_params.get("name")
        if name:
            summoners = Summoner.objects.filter(username__icontains=name)
        else:
            summoners = Summoner.objects.all()
        serializer = SummonerSerializer(summoners, many=True)
        return Response(serializer.data)
    #
class SummonerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Summoner.objects.all().order_by("username")
    serializer_class = SummonerSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Summoner.objects.all().order_by("username")
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(username__icontains=name)
        return queryset
    
    def list(self,request):
        summoner = Summoner.objects.all()
        serializer = SummonerSerializer(summoner, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def get_name(self, request):
        summoner = self.queryset.filter(username__icontains=request.query_params.get("name"))
        serializer = SummonerSerializer(summoner, many=True)
        return Response(serializer.data)
    
