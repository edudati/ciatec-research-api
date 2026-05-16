"""Export job and format constants."""

EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_JSON = "json"

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"

PROJECT_PI_ROLE_CODE = "PI"
SCHEMA_VERSION = "project-timeline-export/1"

CSV_HEADERS = (
    "id",
    "participantProfileId",
    "projectId",
    "enrollmentId",
    "executorId",
    "eventType",
    "sourceType",
    "sourceId",
    "occurredAt",
    "contextJson",
    "createdAt",
)
