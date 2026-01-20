"""Tests for data models."""

import pytest
from src.models.script import Script, ScriptSection, ScriptInput
from src.models.presentation import Presentation, Slide, SyncData, SyncInfo


class TestScriptModels:
    """Tests for script models."""

    def test_script_input_creation(self):
        """Test creating a ScriptInput."""
        input_data = ScriptInput(
            topic="테스트 주제",
            storyline="테스트 스토리라인",
            duration_minutes=5,
            tone="친근한",
        )
        assert input_data.topic == "테스트 주제"
        assert input_data.duration_minutes == 5

    def test_script_section_creation(self):
        """Test creating a ScriptSection."""
        section = ScriptSection(
            section_id=1,
            title="인트로",
            content="안녕하세요, 오늘은...",
            key_points=["포인트 1", "포인트 2"],
            slide_notes="배경 이미지 추가",
            estimated_duration_sec=30.0,
        )
        assert section.section_id == 1
        assert len(section.key_points) == 2

    def test_script_creation_and_duration_calculation(self):
        """Test creating a Script and calculating total duration."""
        sections = [
            ScriptSection(
                section_id=i,
                title=f"섹션 {i}",
                content=f"내용 {i}",
                estimated_duration_sec=30.0,
            )
            for i in range(3)
        ]

        script = Script(
            title="테스트 스크립트",
            description="테스트 설명",
            sections=sections,
        )

        total = script.calculate_total_duration()
        assert total == 90.0
        assert script.total_duration_sec == 90.0

    def test_script_to_full_text(self):
        """Test converting script to full text."""
        sections = [
            ScriptSection(section_id=1, title="A", content="첫 번째 내용"),
            ScriptSection(section_id=2, title="B", content="두 번째 내용"),
        ]
        script = Script(title="테스트", sections=sections)

        full_text = script.to_full_text()
        assert "첫 번째 내용" in full_text
        assert "두 번째 내용" in full_text

    def test_script_get_section_by_id(self):
        """Test getting section by ID."""
        sections = [
            ScriptSection(section_id=1, title="A", content="내용 A"),
            ScriptSection(section_id=2, title="B", content="내용 B"),
        ]
        script = Script(title="테스트", sections=sections)

        section = script.get_section_by_id(2)
        assert section is not None
        assert section.title == "B"

        missing = script.get_section_by_id(999)
        assert missing is None


class TestPresentationModels:
    """Tests for presentation models."""

    def test_slide_creation(self):
        """Test creating a Slide."""
        slide = Slide(
            slide_index=0,
            title="첫 번째 슬라이드",
            content=["포인트 1", "포인트 2"],
            notes="발표자 노트",
        )
        assert slide.slide_index == 0
        assert len(slide.content) == 2

    def test_presentation_creation(self):
        """Test creating a Presentation."""
        slides = [
            Slide(slide_index=i, title=f"슬라이드 {i}")
            for i in range(5)
        ]
        presentation = Presentation(title="테스트 프레젠테이션", slides=slides)

        assert presentation.get_slide_count() == 5

    def test_sync_info_duration(self):
        """Test SyncInfo duration property."""
        sync = SyncInfo(
            slide_index=0,
            section_id=1,
            start_time=10.0,
            end_time=25.0,
        )
        assert sync.duration == 15.0

    def test_sync_data_total_duration(self):
        """Test SyncData total duration calculation."""
        sync_items = [
            SyncInfo(slide_index=0, section_id=1, start_time=0.0, end_time=30.0),
            SyncInfo(slide_index=1, section_id=2, start_time=30.0, end_time=60.0),
            SyncInfo(slide_index=2, section_id=3, start_time=60.0, end_time=90.0),
        ]
        sync_data = SyncData(sync_items=sync_items)

        total = sync_data.calculate_total_duration()
        assert total == 90.0

    def test_sync_data_get_sync_for_slide(self):
        """Test getting sync info for a specific slide."""
        sync_items = [
            SyncInfo(slide_index=0, section_id=1, start_time=0.0, end_time=30.0),
            SyncInfo(slide_index=1, section_id=2, start_time=30.0, end_time=60.0),
        ]
        sync_data = SyncData(sync_items=sync_items)

        sync = sync_data.get_sync_for_slide(1)
        assert sync is not None
        assert sync.section_id == 2

        missing = sync_data.get_sync_for_slide(99)
        assert missing is None
