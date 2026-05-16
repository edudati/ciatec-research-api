"""SQLAlchemy models (import side effects register metadata on Base)."""

from src.models.assessment_record import AssessmentRecord
from src.models.assessment_template import AssessmentTemplate
from src.models.base import Base
from src.models.bestbeat_telemetry import BestbeatEvent, BestbeatPose, BestbeatWorld
from src.models.bubbles_telemetry import BubblesEvent, BubblesPose, BubblesWorld
from src.models.catalog import Game, Level, Preset
from src.models.health_condition import HealthCondition
from src.models.instrument_indication import InstrumentIndication
from src.models.intervention_record import InterventionRecord
from src.models.intervention_template import InterventionTemplate
from src.models.participant_condition import ParticipantCondition
from src.models.participant_enrollment import ParticipantEnrollment
from src.models.participant_profile import ParticipantProfile
from src.models.progress import UserGame, UserLevelProgress
from src.models.project import Project, ProjectGroup, ProjectMember
from src.models.project_export_job import ProjectExportJob
from src.models.question_answer import QuestionAnswer
from src.models.question_item import QuestionItem
from src.models.questionnaire_response import QuestionnaireResponse
from src.models.questionnaire_template import QuestionnaireTemplate
from src.models.self_report_token import SelfReportToken
from src.models.session_match import (
    GameSession,
    Match,
    MatchResult,
    MatchResultDetail,
)
from src.models.timeline_event import TimelineEvent
from src.models.trunktilt_telemetry import TrunkTiltEvent, TrunkTiltPose, TrunkTiltWorld
from src.models.user import AuthUser, RefreshToken, User
from src.models.vocabulary import VocabularyScheme, VocabularyTerm

__all__ = [
    "AssessmentRecord",
    "AssessmentTemplate",
    "AuthUser",
    "Base",
    "BestbeatEvent",
    "BestbeatPose",
    "BestbeatWorld",
    "BubblesEvent",
    "BubblesPose",
    "BubblesWorld",
    "Game",
    "GameSession",
    "HealthCondition",
    "InstrumentIndication",
    "InterventionRecord",
    "InterventionTemplate",
    "Level",
    "Match",
    "MatchResult",
    "MatchResultDetail",
    "ParticipantCondition",
    "ParticipantEnrollment",
    "ParticipantProfile",
    "Preset",
    "Project",
    "ProjectExportJob",
    "ProjectGroup",
    "ProjectMember",
    "QuestionAnswer",
    "QuestionItem",
    "QuestionnaireResponse",
    "QuestionnaireTemplate",
    "RefreshToken",
    "SelfReportToken",
    "TimelineEvent",
    "TrunkTiltEvent",
    "TrunkTiltPose",
    "TrunkTiltWorld",
    "User",
    "UserGame",
    "UserLevelProgress",
    "VocabularyScheme",
    "VocabularyTerm",
]
