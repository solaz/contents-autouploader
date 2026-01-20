"""Script generator using AI services."""

from src.config import Settings, settings
from src.models.script import Script, ScriptInput, ScriptSection
from src.services.ai_service import AIService, get_ai_service
from src.utils.helpers import estimate_speech_duration


SCRIPT_SYSTEM_PROMPT = """당신은 교육 콘텐츠 전문 작가입니다.
주어진 주제와 스토리라인을 바탕으로 일인칭 시점의 강의 대본을 작성합니다.

대본 작성 원칙:
1. 청중에게 직접 말하는 듯한 친근한 어조 사용
2. 복잡한 개념은 쉬운 예시로 설명
3. 각 섹션은 하나의 슬라이드에 대응
4. 섹션별로 명확한 핵심 포인트 3-5개 도출
5. 자연스러운 전환 문구 사용
6. 시작과 끝에 인사말 포함"""


SCRIPT_GENERATION_PROMPT = """다음 정보를 바탕으로 강의 대본을 작성해주세요.

주제: {topic}
스토리라인: {storyline}
목표 시간: {duration_minutes}분
말투/톤: {tone}

다음 JSON 형식으로 응답해주세요:
{{
    "title": "프레젠테이션 제목",
    "description": "영상 설명 (2-3문장)",
    "sections": [
        {{
            "section_id": 1,
            "title": "섹션 제목 (슬라이드 제목으로 사용)",
            "content": "이 섹션의 전체 대본 내용. 청중에게 말하듯이 자연스럽게 작성.",
            "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
            "slide_notes": "슬라이드에 추가할 시각적 요소 제안"
        }}
    ],
    "tags": ["태그1", "태그2", "태그3"]
}}

주의사항:
- 섹션 수는 목표 시간에 맞게 조절 (보통 1분당 1-2개 섹션)
- 각 섹션의 content는 해당 슬라이드를 보여주면서 읽을 대본
- 인트로와 아웃트로 섹션 필수 포함
- 한국어로 작성"""


class ScriptGenerator:
    """Generator for creating scripts from topics and storylines."""

    def __init__(
        self,
        ai_service: AIService | None = None,
        config: Settings | None = None,
    ):
        self.config = config or settings()
        self.ai_service = ai_service or get_ai_service(config=self.config)

    def generate(self, script_input: ScriptInput) -> Script:
        """Generate a complete script from input."""
        prompt = SCRIPT_GENERATION_PROMPT.format(
            topic=script_input.topic,
            storyline=script_input.storyline,
            duration_minutes=script_input.duration_minutes,
            tone=script_input.tone,
        )

        response = self.ai_service.generate_json(prompt, SCRIPT_SYSTEM_PROMPT)

        # Parse sections
        sections = []
        for section_data in response.get("sections", []):
            section = ScriptSection(
                section_id=section_data["section_id"],
                title=section_data["title"],
                content=section_data["content"],
                key_points=section_data.get("key_points", []),
                slide_notes=section_data.get("slide_notes", ""),
                estimated_duration_sec=estimate_speech_duration(section_data["content"]),
            )
            sections.append(section)

        # Create script
        script = Script(
            title=response.get("title", script_input.topic),
            description=response.get("description", ""),
            sections=sections,
            tags=response.get("tags", []),
        )

        script.calculate_total_duration()
        return script

    def generate_from_dict(self, data: dict) -> Script:
        """Generate script from a dictionary input."""
        script_input = ScriptInput(**data)
        return self.generate(script_input)

    def enhance_section(self, section: ScriptSection, instruction: str) -> ScriptSection:
        """Enhance a specific section with additional instructions."""
        prompt = f"""다음 대본 섹션을 개선해주세요.

현재 내용:
제목: {section.title}
대본: {section.content}

개선 지시: {instruction}

같은 JSON 형식으로 개선된 섹션을 반환해주세요:
{{
    "section_id": {section.section_id},
    "title": "개선된 제목",
    "content": "개선된 대본 내용",
    "key_points": ["개선된 포인트 1", "개선된 포인트 2"],
    "slide_notes": "슬라이드 제안"
}}"""

        response = self.ai_service.generate_json(prompt, SCRIPT_SYSTEM_PROMPT)

        return ScriptSection(
            section_id=section.section_id,
            title=response.get("title", section.title),
            content=response.get("content", section.content),
            key_points=response.get("key_points", section.key_points),
            slide_notes=response.get("slide_notes", section.slide_notes),
            estimated_duration_sec=estimate_speech_duration(
                response.get("content", section.content)
            ),
        )
