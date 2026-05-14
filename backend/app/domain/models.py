from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Specialty(StrEnum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    QA = "qa"
    PO = "po"
    DEVOPS = "devops"
    FULLSTACK = "fullstack"


class Level(StrEnum):
    JUNIOR = "junior"
    PLENO = "pleno"
    SENIOR = "senior"
    GOD_TIER = "god-tier"


class CardType(StrEnum):
    FEATURE = "feature"
    BUG = "bug"
    REFACTOR = "refactor"
    INFRA = "infra"
    HOTFIX = "hotfix"


class CardSize(StrEnum):
    P = "P"
    M = "M"
    G = "G"


class Column(StrEnum):
    BACKLOG = "backlog"
    ANALYSIS = "analysis"
    DEVELOPMENT = "development"
    QA = "qa"
    DONE = "done"


class Verdict(StrEnum):
    PLAYING = "playing"
    MASTER_KAIZEN = "master-kaizen"
    SURVIVED = "survived"
    BANKRUPT = "bankrupt"


class KaizenType(StrEnum):
    TRAIN_DEV = "train-dev"
    POKA_YOKE = "poka-yoke"
    QA_AUTOMATION = "qa-automation"
    REST_SPACE = "rest-space"
    WIP_INCREASE = "wip-increase"
    MENTORING = "mentoring"
    INTERNS = "interns"
    MARKETING = "marketing"
    DEVOPS_CULTURE = "devops-culture"
    HEIJUNKA = "heijunka"


@dataclass
class Client:
    id: str
    name: str
    reputation: int
    active: bool = True
    cancellation_sprint: int | None = None


@dataclass
class Developer:
    id: str
    name: str
    specialty: Specialty
    level: Level
    speed: int
    salary: int
    bug_rate: float
    moral: int
    avatar: str
    active: bool = True
    cards_delivered: int = 0
    bugs_generated: int = 0
    tenure_sprints: int = 0
    onboarding_sprints: int = 0
    clean_cards_delivered: int = 0
    god_low_work_streak: int = 0


@dataclass
class Card:
    id: str
    title: str
    card_type: CardType
    size: CardSize
    required_specialties: list[Specialty]
    points_total: int
    progress: int
    value: int
    deadline_sprint: int
    client_id: str
    column: Column
    created_sprint: int
    entered_column_sprint: int
    assigned_dev_ids: list[str] = field(default_factory=list)
    latent_bug: bool = False
    blocked_by_jidoka: bool = False
    cycle_times: dict[str, int] = field(default_factory=dict)


@dataclass
class ScheduledProductionBug:
    source_card_id: str
    source_title: str
    client_id: str
    size: CardSize
    required_specialties: list[Specialty]
    due_sprint: int


@dataclass
class Candidate:
    id: str
    name: str
    specialty: Specialty
    level: Level
    speed: int
    salary: int
    bug_rate: float
    moral: int
    avatar: str
    expires_after_sprint: int | None = None


@dataclass
class SprintMetrics:
    sprint: int
    delivered_cards: int
    throughput_value: int
    oee: float
    lead_time_avg: float
    bugs_in_production: int
    heijunka_bonus: int
    cycle_time_by_column: dict[str, float] = field(default_factory=dict)


@dataclass
class TimelineEvent:
    sprint: int
    kind: str
    message: str


@dataclass
class AndonAlert:
    severity: str
    code: str
    message: str


@dataclass
class KaizenImpact:
    kaizen: KaizenType
    label: str
    before: float
    after: float
    delta: float


@dataclass
class GameState:
    id: str
    seed: int
    sprint: int
    phase: str
    budget: int
    fixed_cost: int
    accumulated_profit: int
    clients: list[Client]
    developers: list[Developer]
    candidates: list[Candidate]
    cards: list[Card]
    wip_limits: dict[str, int]
    kaizen_points: int
    active_kaizens: list[KaizenType]
    metrics_history: list[SprintMetrics]
    timeline: list[TimelineEvent]
    andon_alerts: list[AndonAlert]
    pending_events: list[str]
    consecutive_negative_budget_sprints: int
    heijunka_streak: int
    badges: list[str]
    scheduled_production_bugs: list[ScheduledProductionBug] = field(default_factory=list)
    kaizen_impacts: list[KaizenImpact] = field(default_factory=list)
    verdict: Verdict = Verdict.PLAYING
