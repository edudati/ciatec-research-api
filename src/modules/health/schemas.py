from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field

from src.modules.timeline.cache_metrics import timeline_cache_metrics


class HealthOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    status: Literal["ok"] = "ok"
    timeline_cache_hits: int | None = Field(
        default=None,
        serialization_alias="timelineCacheHits",
    )
    timeline_cache_misses: int | None = Field(
        default=None,
        serialization_alias="timelineCacheMisses",
    )

    @classmethod
    def with_timeline_metrics(cls) -> Self:
        h, m = timeline_cache_metrics.snapshot()
        return cls(timeline_cache_hits=h, timeline_cache_misses=m)
