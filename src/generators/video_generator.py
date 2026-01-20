"""Video generator for combining slides and audio."""

from pathlib import Path

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_audioclips,
    concatenate_videoclips,
    vfx,
)

from src.config import Settings, settings
from src.models.presentation import Presentation, SyncData
from src.utils.helpers import ensure_dir, sanitize_filename


class VideoGenerator:
    """Generator for creating videos from slides and audio."""

    def __init__(self, config: Settings | None = None):
        self.config = config or settings()
        self.video_config = self.config.video

    def generate(
        self,
        presentation: Presentation,
        sync_data: SyncData,
        output_path: Path | str | None = None,
    ) -> Path:
        """Generate a video from presentation and sync data.

        Args:
            presentation: Presentation with slides (must have image_path set)
            sync_data: Synchronization data with timing and audio paths
            output_path: Optional output path for the video

        Returns:
            Path to the generated video file
        """
        if output_path is None:
            output_dir = ensure_dir(Path(self.config.output.base_dir) / "videos")
            output_path = output_dir / f"{sanitize_filename(presentation.title)}.mp4"
        else:
            output_path = Path(output_path)
            ensure_dir(output_path.parent)

        # Create video clips for each slide
        video_clips = []
        audio_clips = []

        for sync_item in sync_data.sync_items:
            slide = presentation.slides[sync_item.slide_index]
            duration = sync_item.duration

            if slide.image_path is None:
                raise ValueError(f"Slide {sync_item.slide_index} has no image path")

            # Create image clip
            img_clip = (
                ImageClip(str(slide.image_path))
                .with_duration(duration)
                .resized((self.video_config.width, self.video_config.height))
            )

            video_clips.append(img_clip)

            # Add audio if available
            if sync_item.audio_file and sync_item.audio_file.exists():
                audio_clip = AudioFileClip(str(sync_item.audio_file))
                # Ensure audio matches the expected duration
                if audio_clip.duration > duration:
                    audio_clip = audio_clip.subclipped(0, duration)
                audio_clips.append(audio_clip)

        # Concatenate video clips
        final_video = concatenate_videoclips(video_clips, method="compose")

        # Add audio if available
        if audio_clips:
            final_audio = concatenate_audioclips(audio_clips)
            final_video = final_video.with_audio(final_audio)

        # Write video file
        final_video.write_videofile(
            str(output_path),
            fps=self.video_config.fps,
            codec=self.video_config.codec,
            audio_codec=self.video_config.audio_codec,
            bitrate=self.video_config.bitrate,
            preset="medium",
            threads=4,
        )

        # Clean up
        final_video.close()
        for clip in video_clips:
            clip.close()
        for clip in audio_clips:
            clip.close()

        return output_path

    def generate_with_transitions(
        self,
        presentation: Presentation,
        sync_data: SyncData,
        output_path: Path | str | None = None,
    ) -> Path:
        """Generate a video with fade transitions between slides.

        Args:
            presentation: Presentation with slides
            sync_data: Synchronization data
            output_path: Optional output path

        Returns:
            Path to the generated video file
        """
        if output_path is None:
            output_dir = ensure_dir(Path(self.config.output.base_dir) / "videos")
            output_path = output_dir / f"{sanitize_filename(presentation.title)}.mp4"
        else:
            output_path = Path(output_path)
            ensure_dir(output_path.parent)

        transition_duration = self.video_config.transition_duration
        video_clips = []
        audio_clips = []

        for i, sync_item in enumerate(sync_data.sync_items):
            slide = presentation.slides[sync_item.slide_index]
            duration = sync_item.duration

            if slide.image_path is None:
                raise ValueError(f"Slide {sync_item.slide_index} has no image path")

            # Create image clip
            img_clip = (
                ImageClip(str(slide.image_path))
                .with_duration(duration)
                .resized((self.video_config.width, self.video_config.height))
            )

            # Add fade in/out for transitions (except first and last)
            if i > 0:
                img_clip = img_clip.with_effects([vfx.CrossFadeIn(transition_duration)])
            if i < len(sync_data.sync_items) - 1:
                img_clip = img_clip.with_effects([vfx.CrossFadeOut(transition_duration)])

            video_clips.append(img_clip)

            # Add audio if available
            if sync_item.audio_file and sync_item.audio_file.exists():
                audio_clip = AudioFileClip(str(sync_item.audio_file))
                if audio_clip.duration > duration:
                    audio_clip = audio_clip.subclipped(0, duration)
                audio_clips.append(audio_clip)

        # Concatenate with crossfade
        final_video = concatenate_videoclips(
            video_clips,
            method="compose",
            padding=-transition_duration,
        )

        # Add audio
        if audio_clips:
            final_audio = concatenate_audioclips(audio_clips)
            final_video = final_video.with_audio(final_audio)

        # Write video file
        final_video.write_videofile(
            str(output_path),
            fps=self.video_config.fps,
            codec=self.video_config.codec,
            audio_codec=self.video_config.audio_codec,
            bitrate=self.video_config.bitrate,
            preset="medium",
            threads=4,
        )

        # Clean up
        final_video.close()
        for clip in video_clips:
            clip.close()
        for clip in audio_clips:
            clip.close()

        return output_path

    def generate_from_single_audio(
        self,
        presentation: Presentation,
        audio_path: Path,
        output_path: Path | str | None = None,
    ) -> Path:
        """Generate video from slides and a single audio file.

        Automatically divides the audio duration equally among slides.

        Args:
            presentation: Presentation with slides
            audio_path: Path to the audio file
            output_path: Optional output path

        Returns:
            Path to the generated video file
        """
        if output_path is None:
            output_dir = ensure_dir(Path(self.config.output.base_dir) / "videos")
            output_path = output_dir / f"{sanitize_filename(presentation.title)}.mp4"
        else:
            output_path = Path(output_path)
            ensure_dir(output_path.parent)

        # Load audio to get duration
        audio_clip = AudioFileClip(str(audio_path))
        total_duration = audio_clip.duration
        num_slides = len(presentation.slides)
        duration_per_slide = total_duration / num_slides

        # Create video clips
        video_clips = []
        for slide in presentation.slides:
            if slide.image_path is None:
                raise ValueError(f"Slide {slide.slide_index} has no image path")

            img_clip = (
                ImageClip(str(slide.image_path))
                .with_duration(duration_per_slide)
                .resized((self.video_config.width, self.video_config.height))
            )
            video_clips.append(img_clip)

        # Concatenate and add audio
        final_video = concatenate_videoclips(video_clips, method="compose")
        final_video = final_video.with_audio(audio_clip)

        # Write video
        final_video.write_videofile(
            str(output_path),
            fps=self.video_config.fps,
            codec=self.video_config.codec,
            audio_codec=self.video_config.audio_codec,
            bitrate=self.video_config.bitrate,
            preset="medium",
            threads=4,
        )

        # Clean up
        final_video.close()
        audio_clip.close()
        for clip in video_clips:
            clip.close()

        return output_path
