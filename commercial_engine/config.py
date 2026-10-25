from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API auth — fails closed when unset (same contract as Media-state-engine)
    commercial_engine_api_key: str = ""

    # Job store (SQLite, WAL). Postgres port tracked separately.
    database_path: str = "data/commercial_engine.db"

    # Manifests are only ever read from this directory (no arbitrary paths).
    manifests_dir: str = "manifests"
    # Pre-supplied footage: {dir}/{scene_id}.mp4
    screen_recordings_dir: str = "assets/screen_recordings"
    broll_dir: str = "assets/broll"
    # Generated intermediates + finished commercials
    work_dir: str = "data/work"
    output_dir: str = "data/outputs"

    # ElevenLabs — narrator for every scene (presenter lip-syncs to this audio)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    elevenlabs_url: str = "https://api.elevenlabs.io/v1/text-to-speech"

    # HeyGen — stock presenter avatar (no custom likeness / reference pack)
    heygen_api_key: str = ""
    heygen_api_url: str = "https://api.heygen.com"
    heygen_upload_url: str = "https://upload.heygen.com"
    heygen_avatar_id: str = ""
    heygen_background_color: str = "#0B0F14"
    heygen_poll_interval_seconds: float = 10.0
    heygen_timeout_seconds: float = 900.0

    # B-roll provider: "files" (pre-supplied clips) until a generator API is verified
    broll_provider: str = "files"

    # Output format
    video_width: int = 1080
    video_height: int = 1920
    video_fps: int = 30
    scene_tail_seconds: float = 0.25

    # HUD overlay (electric blue box, white text)
    hud_font_file: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    hud_font_size: int = 64
    hud_box_color: str = "0x00B4FF@0.85"
    hud_text_color: str = "white"
    hud_max_chars: int = 32

    # End card
    brand_name: str = "JobCommand"
    cta_text: str = "Book. Dispatch. Get paid."
    cta_url: str = "jobcommand.app"
    end_card_seconds: float = 2.5
    end_card_background: str = "0x0B0F14"

    # Concurrency caps (rate limits), not a global lock
    elevenlabs_concurrency: int = 3
    heygen_concurrency: int = 2
    ffmpeg_concurrency: int = 2

    # Worker
    worker_poll_interval_seconds: float = 2.0
    stale_claim_seconds: int = 3600
    provider_max_attempts: int = 3
    provider_retry_base_seconds: float = 2.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def path(self, name: str) -> Path:
        p = Path(getattr(self, name))
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
