from django.db import models
from django.utils import timezone


class Patch(models.Model):
    """
    Represents a League of Legends game patch/version.
    Used to track meta changes over time and associate matches with specific patches.
    """
    version = models.CharField(max_length=16, unique=True, primary_key=True)  # e.g., "14.23", "15.1"
    release_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)  # True for current patch
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-version']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['-version']),
        ]

    def __str__(self) -> str:
        return f"Patch {self.version}"


class Summoner(models.Model):
    puuid = models.CharField(primary_key=True, max_length=72)
    username = models.CharField(max_length=16)
    server = models.CharField(max_length=5)
    icon = models.URLField()
    ranked_solo_rank = models.CharField(max_length=32, default="Unranked")
    ranked_flex_rank = models.CharField(max_length=32, default="Unranked")
    ranked_solo_wins = models.PositiveSmallIntegerField(default=0)
    ranked_solo_loses = models.PositiveSmallIntegerField(default=0)
    ranked_flex_wins = models.PositiveSmallIntegerField(default=0)
    ranked_flex_loses = models.PositiveSmallIntegerField(default=0)
    quickplay_wins = models.PositiveSmallIntegerField(default=0)
    quickplay_loses = models.PositiveSmallIntegerField(default=0)
    normal_wins = models.PositiveSmallIntegerField(default=0)
    normal_loses = models.PositiveSmallIntegerField(default=0)
    aram_wins = models.PositiveSmallIntegerField(default=0)
    aram_loses = models.PositiveSmallIntegerField(default=0)
    arena_wins = models.PositiveSmallIntegerField(default=0)
    arena_loses = models.PositiveSmallIntegerField(default=0)
    clash_wins = models.PositiveSmallIntegerField(default=0)
    clash_loses = models.PositiveSmallIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['puuid']),  # Already primary key but for explicit lookup
            models.Index(fields=['username']),  # Search by summoner name
            models.Index(fields=['server']),  # Filter by region/server
            models.Index(fields=['server', 'username']),  # Combined region + name lookup
        ]

    def __str__(self) -> str:
        return self.username


class Match(models.Model):
    """
    Represents a single League of Legends match.
    Stores basic match information and metadata for analysis.
    """
    WINNER_CHOICES = (
        (100, "Blue"),
        (200, "Red"),
    )

    # Queue type constants from Riot API
    # https://static.developer.riotgames.com/docs/lol/queues.json
    QUEUE_TYPE_CHOICES = [
        (400, 'Normal Draft'),
        (420, 'Ranked Solo/Duo'),
        (430, 'Normal Blind'),
        (440, 'Ranked Flex'),
        (450, 'ARAM'),
        (700, 'Clash'),
        (720, 'ARAM Clash'),
        (830, 'Intro Bots'),
        (840, 'Beginner Bots'),
        (850, 'Intermediate Bots'),
        (900, 'URF'),
        (1020, 'One for All'),
        (1300, 'Nexus Blitz'),
        (1400, 'Ultimate Spellbook'),
        (1700, 'Arena'),
        (1900, 'Pick URF'),
    ]

    id = models.CharField(primary_key=True, max_length=32)
    match_timestamp = models.DateTimeField(db_index=True, null=True, blank=True)  # When the match was played
    duration = models.DurationField()
    winner_team = models.PositiveSmallIntegerField(choices=WINNER_CHOICES)
    time_lane = models.CharField(max_length=100)
    gold_diff = models.PositiveBigIntegerField()

    # New fields for better match tracking
    queue_type = models.IntegerField(choices=QUEUE_TYPE_CHOICES, null=True, blank=True, db_index=True)
    region = models.CharField(max_length=10, null=True, blank=True, db_index=True)  # e.g., "NA1", "EUW1", "KR"
    patch_version = models.ForeignKey(
        Patch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches",
        db_index=True,
    )

    # Raw match data for future reprocessing
    raw_data = models.JSONField(null=True, blank=True)  # Store complete match JSON from Riot API

    summoners = models.ManyToManyField(
        Summoner,
        through="MatchSummoners",
        through_fields=("match", "summoner"),
        related_name="matches",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['-match_timestamp']),  # For recent matches queries
            models.Index(fields=['queue_type', '-match_timestamp']),  # Filter by queue + time
            models.Index(fields=['patch_version', 'queue_type']),  # Meta analysis
            models.Index(fields=['region', '-match_timestamp']),  # Regional queries
        ]

    def __str__(self) -> str:
        return f"Match {self.pk}"

class Champion(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=32, default = "")
    title = models.CharField(max_length=64, default = "")
    description = models.CharField(max_length=2550, default = "")
    attack = models.PositiveSmallIntegerField(default=0)
    defense = models.PositiveSmallIntegerField(default=0)
    magic = models.PositiveSmallIntegerField(default=0)
    difficulty = models.PositiveSmallIntegerField(default=0)
    tags = models.JSONField(default=list, blank=True)
    partype = models.CharField(max_length=64, default = "")
    hp = models.FloatField(default=0)
    hp_per_level = models.FloatField(default=0)
    mp = models.FloatField(default=0)
    mp_per_level = models.FloatField(default=0)
    move_speed = models.FloatField(default=0)
    armor = models.FloatField(default=0)
    armor_per_level = models.FloatField(default=0)
    spell_block = models.FloatField(default=0)
    spell_block_per_level = models.FloatField(default=0)
    attack_range = models.PositiveSmallIntegerField(default=0)
    hp_regen = models.FloatField(default=0)
    hp_regen_per_level = models.FloatField(default=0)
    mp_regen = models.FloatField(default=0)
    mp_regen_per_level = models.FloatField(default=0)
    crit = models.FloatField(default=0)
    crit_per_level = models.FloatField(default=0)
    attack_damage = models.FloatField(default=0)
    attack_damage_per_level = models.FloatField(default=0)
    attack_speed_per_level = models.FloatField(default=0)
    attack_speed = models.FloatField(default=0)
    wins = models.FloatField(default=0)
    bans = models.FloatField(default=0)
    picks = models.FloatField(default=0)
    icon = models.URLField(default="")
    summoners = models.ManyToManyField(
        Summoner,
        through="ChampionStat",
        through_fields=("champion", "summoner"),
        related_name="champions",
    )

    class Meta:
        indexes = [
            models.Index(fields=['name']),  # Search by champion name
            models.Index(fields=['id']),  # Already primary key but explicit for clarity
        ]

    def __str__(self) -> str:
        return self.name



class Rune(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    rune_name = models.CharField(max_length=20)
    rune_value = models.PositiveIntegerField()
    rune_description = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.rune_name


class Item(models.Model):
    id = models.PositiveIntegerField(primary_key=True, default=0)
    name = models.CharField(max_length=100, default = "")
    plaintext = models.CharField(max_length=255, blank=True, default="")
    value = models.PositiveSmallIntegerField(default=0)
    description = models.TextField(blank=True, default="")  # HTML de Riot
    colloq = models.CharField(max_length=255, blank=True)  # términos de búsqueda
    # Propiedades varias del ítem
    stacks = models.PositiveIntegerField(null=True, blank=True)
    depth = models.PositiveIntegerField(null=True, blank=True)
    consumed = models.BooleanField(default=False, null=True)
    consume_on_full = models.BooleanField(default=False, blank=True, null=True)
    in_store = models.BooleanField(default=True, null=True)
    hide_from_all = models.BooleanField(default=False, null=True)
    # Requisitos especiales
    required_champion = models.CharField(max_length=32, blank=True)
    required_ally = models.CharField(max_length=32, blank=True)
    special_recipe = models.PositiveIntegerField(null=True, blank=True)
    required_buff_currency_name = models.CharField(max_length=64, blank=True)
    required_buff_currency_cost = models.PositiveIntegerField(null=True, blank=True)
    # gold: { "base": int, "purchasable": bool, "total": int, "sell": int }
    base_gold = models.IntegerField(default = 0)
    purchasable = models.BooleanField(default = False)
    total_gold = models.IntegerField(default = 0)
    sell_gold = models.IntegerField(default = 0)
    # image: { "full": str, "sprite": str, "group": str, "x": int, "y": int, "w": int, "h": int }
    image = models.URLField(default = "")
        # stats: diccionario de stats (p.ej. AbilityHaste, MagicResist, etc.)
    stats = models.JSONField(default=dict, blank=True)
    # effect: efectos/variables usadas en la description (p.ej. "Effect1Amount": "15")
    effect = models.JSONField(default=dict, blank=True, null=True)
    # Listas y banderas por mapa / tags
    # into / from: listas de IDs de ítems (construcciones)
    builds_into = models.JSONField(default=list, blank=True, null=True)  # "into"
    builds_from = models.JSONField(default=list, blank=True, null=True)  # "from"
    # tags: lista de etiquetas (Armor, AttackSpeed, Mana, etc.)
    tags = models.JSONField(default=list, blank=True)
    # maps: {"11": true/false, "12": true/false, ...}
    maps = models.JSONField(default=dict, blank=True)
    # Metadatos opcionales




    def __str__(self) -> str:
        return self.name


class MatchSummoners(models.Model):
    """
    Junction table linking Summoners to Matches with detailed performance data.
    Each record represents one player's performance in a specific match.
    """

    # Role and lane constants from Riot API
    ROLE_CHOICES = [
        ('TOP', 'Top'),
        ('JUNGLE', 'Jungle'),
        ('MIDDLE', 'Middle'),
        ('BOTTOM', 'Bottom'),
        ('UTILITY', 'Support'),  # Riot now calls support "UTILITY"
    ]

    LANE_CHOICES = [
        ('TOP', 'Top Lane'),
        ('JUNGLE', 'Jungle'),
        ('MIDDLE', 'Mid Lane'),
        ('BOTTOM', 'Bot Lane'),
        ('NONE', 'None'),  # For ARAM, URF, etc.
    ]

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="match_entries",
    )
    summoner = models.ForeignKey(
        Summoner,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    champion = models.ForeignKey(
        Champion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="champion",
    )

    # Position tracking for role-based analytics
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True, blank=True, db_index=True)
    lane = models.CharField(max_length=10, choices=LANE_CHOICES, null=True, blank=True)
    item0 = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="item0",
    )
    item1 = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="item1",
    )
    item2 = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="item2",
    )
    item3 = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="item3",
    )
    item4 = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="item4",
    )
    item5 = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="item5",
    )
    item6 = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="item6",
    )

    # Runes and summoner spells
    # rune_ids: JSONField storing primary and secondary rune tree selections
    # Example: {"primary": [8100, 8112, 8143, 8136, 8105], "secondary": [8300, 8304], "shards": [5008, 5008, 5002]}
    rune_ids = models.JSONField(null=True, blank=True, default=dict)

    # summoner_spell_ids: List of two summoner spell IDs (e.g., [4, 14] for Flash + Ignite)
    # Common IDs: Flash=4, Ignite=14, Teleport=12, Heal=7, Barrier=21, Exhaust=3, Smite=11
    summoner_spell_ids = models.JSONField(null=True, blank=True, default=list)

    skill_order = models.CharField(max_length=255, blank=True, default="")
    cs = models.PositiveIntegerField(default=0)
    wards_used = models.PositiveSmallIntegerField(default=0)
    vision_points = models.PositiveSmallIntegerField(default=0)
    damage_dealt = models.BigIntegerField(default=0)
    damage_received = models.BigIntegerField(default=0)
    damage_healed = models.BigIntegerField(default=0)
    damage_mitigated = models.BigIntegerField(default=0)
    game_type = models.CharField(max_length=16)
    winner = models.BooleanField(default=False)
    ranked_points = models.PositiveBigIntegerField(default=0)
    kills = models.PositiveSmallIntegerField(default=0)
    deaths = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    total_gold = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("match", "summoner"),
                name="uniq_match_summoner",
            ),
        ]
        indexes = [
            models.Index(
                fields=("match",),
                name="lol_navo_ma_match_i_a43a6d_idx",
            ),
            models.Index(
                fields=("summoner",),
                name="lol_navo_ma_summone_608e1a_idx",
            ),
            models.Index(
                fields=("match", "summoner"),
                name="lol_navo_ma_match_i_e32db8_idx",
            ),
            # New indexes for role-based queries
            models.Index(
                fields=("champion", "role"),
                name="lol_navo_ma_champ_role_idx",
            ),
            models.Index(
                fields=("summoner", "champion", "role"),
                name="lol_navo_ma_s_c_r_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.match_id} | {self.summoner_id}"


class ChampionStat(models.Model):
    """
    Tracks individual summoner performance on specific champions.
    Can be aggregated by patch for historical performance tracking.
    """
    summoner = models.ForeignKey(
        Summoner,
        on_delete=models.CASCADE,
        related_name="stats",
    )
    champion = models.ForeignKey(
        Champion,
        on_delete=models.CASCADE,
        related_name="summoner_stats",
    )
    patch_version = models.ForeignKey(
        Patch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="champion_stats",
    )
    point = models.PositiveBigIntegerField(default=0)
    winrate = models.FloatField(default=0.0)
    kda = models.FloatField(default=0.0)
    games = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("summoner", "champion"),
                name="uniq_summoner_champion",
            ),
        ]
        indexes = [
            models.Index(
                fields=("summoner",),
                name="lol_navo_ch_summone_7dee11_idx",
            ),
            models.Index(
                fields=("champion",),
                name="lol_navo_ch_champio_e7a704_idx",
            ),
            models.Index(
                fields=("summoner", "champion"),
                name="lol_navo_ch_summone_3c06f4_idx",
            ),
            models.Index(
                fields=("summoner", "patch_version"),
                name="lol_navo_ch_summ_patch_idx",
            ),
            models.Index(
                fields=("champion", "patch_version"),
                name="lol_navo_ch_champ_patch_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.summoner_id} | {self.id}"


# ============================================================================
# AGGREGATED STATISTICS MODELS
# These models store precomputed statistics for fast query performance
# ============================================================================


class ChampionRoleStats(models.Model):
    """
    Aggregated statistics for champion performance by role and patch.
    Precomputed for fast tier list and meta analysis queries.
    """
    champion = models.ForeignKey(
        Champion,
        on_delete=models.CASCADE,
        related_name="role_stats",
    )
    role = models.CharField(max_length=10, choices=MatchSummoners.ROLE_CHOICES)
    patch = models.ForeignKey(
        Patch,
        on_delete=models.CASCADE,
        related_name="champion_role_stats",
    )
    queue_type = models.IntegerField(choices=Match.QUEUE_TYPE_CHOICES, default=420)  # Default to Ranked Solo

    # Performance metrics
    games_played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    winrate = models.FloatField(default=0.0)  # Percentage: 0-100
    pickrate = models.FloatField(default=0.0)  # Percentage: 0-100
    banrate = models.FloatField(default=0.0)  # Percentage: 0-100

    # Aggregated stats
    avg_kills = models.FloatField(default=0.0)
    avg_deaths = models.FloatField(default=0.0)
    avg_assists = models.FloatField(default=0.0)
    avg_kda = models.FloatField(default=0.0)
    avg_cs = models.FloatField(default=0.0)
    avg_damage_dealt = models.BigIntegerField(default=0)
    avg_gold = models.BigIntegerField(default=0)

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("champion", "role", "patch", "queue_type"),
                name="uniq_champion_role_patch_queue",
            ),
        ]
        indexes = [
            models.Index(fields=["patch", "queue_type", "role", "-winrate"]),  # Tier lists
            models.Index(fields=["champion", "role", "-patch"]),  # Champion history
            models.Index(fields=["patch", "queue_type", "-games_played"]),  # Most played
            models.Index(fields=["patch", "queue_type", "-pickrate"]),  # Popularity
            models.Index(fields=["patch", "queue_type", "-banrate"]),  # Ban priority
        ]
        ordering = ['-patch', '-winrate']

    def __str__(self) -> str:
        return f"{self.champion.name} - {self.role} - Patch {self.patch.version}"


class BuildStats(models.Model):
    """
    Tracks item build performance for champions by role and patch.
    Used to generate optimal build recommendations.
    """
    champion = models.ForeignKey(
        Champion,
        on_delete=models.CASCADE,
        related_name="build_stats",
    )
    role = models.CharField(max_length=10, choices=MatchSummoners.ROLE_CHOICES)
    patch = models.ForeignKey(
        Patch,
        on_delete=models.CASCADE,
        related_name="build_stats",
    )
    queue_type = models.IntegerField(choices=Match.QUEUE_TYPE_CHOICES, default=420)

    # Build definition
    # item_build: List of item IDs in build order (e.g., [3078, 3031, 3036, 3094, 3026, 6333])
    item_build = models.JSONField()

    # Build category
    build_type = models.CharField(
        max_length=20,
        choices=[
            ('CORE', 'Core Build'),  # First 2-3 items
            ('FULL', 'Full Build'),  # Complete 6-item build
            ('SITUATIONAL', 'Situational'),  # Alternative items
        ],
        default='CORE',
    )

    # Performance metrics
    games_played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    winrate = models.FloatField(default=0.0)
    avg_damage = models.BigIntegerField(default=0)
    avg_gold = models.BigIntegerField(default=0)

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["champion", "role", "patch", "-games_played"]),  # Popular builds
            models.Index(fields=["champion", "role", "patch", "-winrate"]),  # Best builds
            models.Index(fields=["patch", "queue_type", "build_type"]),  # Meta builds
        ]
        ordering = ['-patch', '-winrate']

    def __str__(self) -> str:
        item_count = len(self.item_build) if isinstance(self.item_build, list) else 0
        return f"{self.champion.name} - {self.role} - {item_count} items - {self.winrate:.1f}% WR"


class MatchupStats(models.Model):
    """
    Tracks champion vs champion performance by role and patch.
    Used for counter-pick recommendations and matchup analysis.
    """
    champion = models.ForeignKey(
        Champion,
        on_delete=models.CASCADE,
        related_name="matchup_stats_as_player",
    )
    opponent = models.ForeignKey(
        Champion,
        on_delete=models.CASCADE,
        related_name="matchup_stats_as_opponent",
    )
    role = models.CharField(max_length=10, choices=MatchSummoners.ROLE_CHOICES)
    patch = models.ForeignKey(
        Patch,
        on_delete=models.CASCADE,
        related_name="matchup_stats",
    )
    queue_type = models.IntegerField(choices=Match.QUEUE_TYPE_CHOICES, default=420)

    # Matchup performance
    games_played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    winrate = models.FloatField(default=0.0)  # Champion's winrate against opponent

    # Performance deltas (compared to champion's overall performance in role)
    winrate_delta = models.FloatField(default=0.0)  # Difference from average winrate
    avg_kills_delta = models.FloatField(default=0.0)
    avg_deaths_delta = models.FloatField(default=0.0)
    avg_cs_delta = models.FloatField(default=0.0)

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("champion", "opponent", "role", "patch", "queue_type"),
                name="uniq_matchup",
            ),
        ]
        indexes = [
            models.Index(fields=["champion", "role", "patch", "-winrate"]),  # Best matchups
            models.Index(fields=["champion", "role", "patch", "winrate"]),  # Worst matchups (counters)
            models.Index(fields=["opponent", "role", "patch", "-winrate"]),  # Who counters this champion
            models.Index(fields=["patch", "queue_type", "-games_played"]),  # Most common matchups
        ]
        ordering = ['-patch', '-winrate']

    def __str__(self) -> str:
        return f"{self.champion.name} vs {self.opponent.name} - {self.role} - {self.winrate:.1f}% WR"
