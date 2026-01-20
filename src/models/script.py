"""Script data models."""

from pydantic import BaseModel, Field


class ScriptInput(BaseModel):
    """Input for script generation."""

    topic: str = Field(..., description="Main topic of the presentation")
    storyline: str = Field(..., description="Brief storyline or outline")
    duration_minutes: int = Field(default=10, description="Target duration in minutes")
    tone: str = Field(default="친근하고 설득력 있는", description="Tone and style of the script")
    language: str = Field(default="ko", description="Language code")


class ScriptSection(BaseModel):
    """A section of the script corresponding to one slide."""

    section_id: int = Field(..., description="Unique section identifier")
    title: str = Field(..., description="Section title for the slide")
    content: str = Field(..., description="Full narration text for this section")
    key_points: list[str] = Field(
        default_factory=list, description="Key bullet points for the slide"
    )
    slide_notes: str = Field(default="", description="Additional notes for slide design")
    estimated_duration_sec: float = Field(
        default=0.0, description="Estimated duration in seconds"
    )


class Script(BaseModel):
    """Complete script with all sections."""

    title: str = Field(..., description="Presentation title")
    description: str = Field(default="", description="Brief description of the content")
    sections: list[ScriptSection] = Field(
        default_factory=list, description="List of script sections"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    total_duration_sec: float = Field(default=0.0, description="Total estimated duration")

    def calculate_total_duration(self) -> float:
        """Calculate and update total duration from sections."""
        self.total_duration_sec = sum(s.estimated_duration_sec for s in self.sections)
        return self.total_duration_sec

    def to_full_text(self) -> str:
        """Convert script to full narration text."""
        return "\n\n".join(section.content for section in self.sections)

    def get_section_by_id(self, section_id: int) -> ScriptSection | None:
        """Get a section by its ID."""
        for section in self.sections:
            if section.section_id == section_id:
                return section
        return None
