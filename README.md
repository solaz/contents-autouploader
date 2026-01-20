# Contents Auto-Uploader

주제와 스토리라인을 입력하면 대본 생성 → 프레젠테이션 생성 → 영상 제작 → YouTube 업로드까지 자동화하는 파이프라인입니다.

## 기능

- **대본 생성**: AI(Claude/OpenAI/Ollama)를 활용한 일인칭 강의 스타일 대본 자동 생성
- **프레젠테이션 생성**: 대본 기반 PowerPoint 자동 생성
- **TTS 음성 합성**: ElevenLabs, Google TTS, OpenAI TTS, 로컬 TTS(pyttsx3) 지원
- **영상 제작**: 슬라이드와 음성을 동기화한 MP4 영상 생성
- **YouTube 업로드**: 완성된 영상 자동 업로드

## 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/contents-autouploader.git
cd contents-autouploader

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -e .
```

## 설정

### 1. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 편집하여 API 키를 입력:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
```

### 2. 설정 파일 커스터마이징

`config/config.yaml`에서 세부 설정 조정 가능:

```yaml
ai:
  provider: "claude"  # claude, openai, ollama

tts:
  provider: "openai"  # elevenlabs, google, openai, local

youtube:
  privacy_status: "private"  # public, private, unlisted
```

## 사용법

### 전체 파이프라인 실행

```bash
# 기본 실행
python -m src.main generate \
  --topic "시간 관리의 중요성" \
  --storyline "시간 낭비의 문제점 → 효과적인 시간 관리 방법 → 실천 팁" \
  --duration 10

# YouTube 업로드 포함
python -m src.main generate \
  --topic "시간 관리의 중요성" \
  --storyline "시간 낭비 문제 → 관리 방법 → 실천 팁" \
  --duration 10 \
  --upload \
  --privacy private
```

### 개별 단계 실행

```bash
# 1. 대본 생성
python -m src.main script \
  --topic "시간 관리" \
  --storyline "문제점 → 해결책 → 실천" \
  --output script.json

# 2. 프레젠테이션 생성
python -m src.main ppt \
  --script script.json \
  --output presentation.pptx

# 3. TTS 음성 생성
python -m src.main tts \
  --script script.json \
  --provider openai

# 4. 영상 생성
python -m src.main video \
  --script script.json

# 5. YouTube 업로드
python -m src.main upload \
  --video output/videos/시간_관리.mp4 \
  --title "시간 관리의 중요성" \
  --description "효과적인 시간 관리 방법을 알아봅니다."
```

## 로컬 개발 (Ollama / Local TTS)

개발 비용 절감을 위해 로컬 LLM과 로컬 TTS를 사용할 수 있습니다.

### 로컬 개발용 .env

```bash
cp .env.local.example .env
```

### Ollama 설치 및 실행 (macOS)

```bash
brew install ollama
ollama serve
ollama pull llama3.2
```

### 설정 예시

로컬 개발용 샘플 설정을 사용하려면:

```bash
python -m src.main --config config/config.local.yaml script --topic "테스트" --storyline "소개 → 본문 → 마무리"
```

또는 `config/config.yaml`에서 provider를 변경:

```yaml
ai:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434/v1"
    model: "llama3.2"

tts:
  provider: "local"
  local:
    rate: 150
    volume: 1.0
```

로컬 TTS는 `.wav` 파일을 생성합니다.

## 프로젝트 구조

```
contents-autouploader/
├── src/
│   ├── main.py                 # CLI 인터페이스
│   ├── config.py               # 설정 관리
│   ├── models/                 # 데이터 모델
│   │   ├── script.py
│   │   └── presentation.py
│   ├── generators/             # 생성기
│   │   ├── script_generator.py
│   │   ├── ppt_generator.py
│   │   ├── tts_generator.py
│   │   └── video_generator.py
│   ├── services/               # 서비스
│   │   ├── ai_service.py
│   │   ├── sync_service.py
│   │   └── youtube_service.py
│   └── utils/
│       └── helpers.py
├── config/
│   └── config.yaml
├── tests/
├── output/                     # 생성물 저장
└── requirements.txt
```

## API 키 발급 안내

1. **Claude API**: [Anthropic Console](https://console.anthropic.com/)
2. **OpenAI API**: [OpenAI Platform](https://platform.openai.com/)
3. **ElevenLabs API**: [ElevenLabs](https://elevenlabs.io/)
4. **YouTube API**: [Google Cloud Console](https://console.cloud.google.com/)
   - YouTube Data API v3 활성화
   - OAuth 2.0 클라이언트 ID 생성

## 개발

```bash
# 개발 의존성 설치
pip install -e ".[dev]"

# 테스트 실행
pytest tests/ -v

# 코드 포맷팅
black src/ tests/
ruff check src/ tests/
```

## 라이선스

MIT License
