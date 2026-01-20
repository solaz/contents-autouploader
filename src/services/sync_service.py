"""Synchronization service for matching slides with audio."""

from pathlib import Path

from src.models.presentation import Presentation, Slide, SyncData, SyncInfo
from src.models.script import Script


class SyncService:
    """Service for synchronizing slides with audio timing."""

    def create_sync_data(
        self,
        script: Script,
        presentation: Presentation,
        audio_durations: list[tuple[int, Path, float]],
    ) -> SyncData:
        """Create synchronization data from script, presentation, and audio.

        Args:
            script: The script with sections
            presentation: The presentation with slides
            audio_durations: List of (section_id, audio_path, duration) tuples

        Returns:
            SyncData with timing information for each slide
        """
        sync_items = []
        current_time = 0.0

        # Create a mapping from section_id to audio info
        audio_map = {section_id: (path, duration) for section_id, path, duration in audio_durations}

        # First slide is usually the title slide
        # Map it to a short intro or skip
        if len(presentation.slides) > len(script.sections):
            # Title slide gets a short duration
            title_duration = 3.0  # 3 seconds for title slide
            sync_items.append(
                SyncInfo(
                    slide_index=0,
                    section_id=0,
                    start_time=current_time,
                    end_time=current_time + title_duration,
                    audio_file=None,
                )
            )
            current_time += title_duration
            slide_offset = 1
        else:
            slide_offset = 0

        # Map sections to slides
        for i, section in enumerate(script.sections):
            slide_index = i + slide_offset

            if slide_index >= len(presentation.slides):
                break

            audio_path, duration = audio_map.get(section.section_id, (None, section.estimated_duration_sec))

            sync_items.append(
                SyncInfo(
                    slide_index=slide_index,
                    section_id=section.section_id,
                    start_time=current_time,
                    end_time=current_time + duration,
                    audio_file=audio_path,
                )
            )

            current_time += duration

        sync_data = SyncData(sync_items=sync_items)
        sync_data.calculate_total_duration()

        return sync_data

    def create_simple_sync(
        self,
        presentation: Presentation,
        durations: list[float],
    ) -> SyncData:
        """Create simple sync data with given durations for each slide.

        Args:
            presentation: The presentation with slides
            durations: List of durations in seconds for each slide

        Returns:
            SyncData with timing information
        """
        if len(durations) != len(presentation.slides):
            raise ValueError(
                f"Number of durations ({len(durations)}) must match "
                f"number of slides ({len(presentation.slides)})"
            )

        sync_items = []
        current_time = 0.0

        for i, (slide, duration) in enumerate(zip(presentation.slides, durations)):
            sync_items.append(
                SyncInfo(
                    slide_index=i,
                    section_id=i,
                    start_time=current_time,
                    end_time=current_time + duration,
                    audio_file=None,
                )
            )
            current_time += duration

        sync_data = SyncData(sync_items=sync_items)
        sync_data.calculate_total_duration()

        return sync_data

    def update_audio_paths(
        self,
        sync_data: SyncData,
        audio_files: dict[int, Path],
    ) -> SyncData:
        """Update sync data with audio file paths.

        Args:
            sync_data: Existing sync data
            audio_files: Mapping of section_id to audio file path

        Returns:
            Updated SyncData
        """
        for sync_item in sync_data.sync_items:
            if sync_item.section_id in audio_files:
                sync_item.audio_file = audio_files[sync_item.section_id]

        return sync_data

    def adjust_timing(
        self,
        sync_data: SyncData,
        actual_durations: dict[int, float],
    ) -> SyncData:
        """Adjust timing based on actual audio durations.

        Args:
            sync_data: Existing sync data
            actual_durations: Mapping of section_id to actual duration

        Returns:
            Updated SyncData with adjusted timing
        """
        current_time = 0.0

        for sync_item in sync_data.sync_items:
            if sync_item.section_id in actual_durations:
                duration = actual_durations[sync_item.section_id]
            else:
                duration = sync_item.duration

            sync_item.start_time = current_time
            sync_item.end_time = current_time + duration
            current_time += duration

        sync_data.calculate_total_duration()
        return sync_data

    def get_slide_at_time(self, sync_data: SyncData, time: float) -> int | None:
        """Get the slide index that should be displayed at a given time.

        Args:
            sync_data: Sync data with timing
            time: Time in seconds

        Returns:
            Slide index or None if time is out of range
        """
        for sync_item in sync_data.sync_items:
            if sync_item.start_time <= time < sync_item.end_time:
                return sync_item.slide_index
        return None
