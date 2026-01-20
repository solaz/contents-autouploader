"""Presentation and synchronization data models."""

from pathlib import Path

from pydantic import BaseModel, Field


class Slide(BaseModel):
    """A single slide in the presentation."""

    slide_index: int = Field(..., description="Zero-based slide index")
    title: str = Field(..., description="Slide title")
    content: list[str] = Field(default_factory=list, description="Bullet points or content")
    notes: str = Field(default="", description="Speaker notes (script text)")
    image_path: Path | None = Field(default=None, description="Path to slide image for video")


class Presentation(BaseModel):
    """Complete presentation with all slides."""

    title: str = Field(..., description="Presentation title")
    slides: list[Slide] = Field(default_factory=list, description="List of slides")
    file_path: Path | None = Field(default=None, description="Path to the .pptx file")

    def get_slide_count(self) -> int:
        """Get total number of slides."""
        return len(self.slides)


class SyncInfo(BaseModel):
    """Synchronization information for a slide."""

    slide_index: int = Field(..., description="Zero-based slide index")
    section_id: int = Field(..., description="Corresponding script section ID")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    audio_file: Path | None = Field(default=None, description="Path to audio file for this section")

    @property
    def duration(self) -> float:
        """Get duration of this segment."""
        return self.end_time - self.start_time


class SyncData(BaseModel):
    """Complete synchronization data for the video."""

    sync_items: list[SyncInfo] = Field(
        default_factory=list, description="List of sync information"
    )
    total_duration: float = Field(default=0.0, description="Total video duration")

    def calculate_total_duration(self) -> float:
        """Calculate total duration from sync items."""
        if self.sync_items:
            self.total_duration = max(item.end_time for item in self.sync_items)
        return self.total_duration

    def get_sync_for_slide(self, slide_index: int) -> SyncInfo | None:
        """Get sync info for a specific slide."""
        for item in self.sync_items:
            if item.slide_index == slide_index:
                return item
        return None
