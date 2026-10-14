import hmac
import os
from dataclasses import dataclass

SERVER_NAME = "neuralhud"
SERVER_VERSION = "0.1.0"


@dataclass(frozen=True)
class Settings:
    database_url: str
    # label -> token. Labels identify the caller in the job_events audit log.
    tokens: dict[str, str]
    allowed_origins: frozenset[str]

    def actor_for(self, presented: str) -> str | None:
        """Return the label for a presented bearer token, or None."""
        match = None
        for label, token in self.tokens.items():
            # Compare against every token so timing doesn't reveal which matched.
            if hmac.compare_digest(presented.encode(), token.encode()):
                match = label
        return match


def parse_tokens(raw: str) -> dict[str, str]:
    """Parse NEURALHUD_MCP_TOKENS: "label:token,label2:token2" or a bare token."""
    tokens: dict[str, str] = {}
    for i, part in enumerate(p.strip() for p in raw.split(",")):
        if not part:
            continue
        label, sep, token = part.partition(":")
        if not sep:
            label, token = ("default" if i == 0 else f"token{i}"), part
        if len(token) < 32:
            raise ValueError(f"token for '{label}' is shorter than 32 characters")
        tokens[label] = token
    return tokens


def load_settings() -> Settings:
    return Settings(
        database_url=os.environ.get("DATABASE_URL", ""),
        tokens=parse_tokens(os.environ.get("NEURALHUD_MCP_TOKENS", "")),
        allowed_origins=frozenset(
            o.strip() for o in os.environ.get("NEURALHUD_ALLOWED_ORIGINS", "").split(",") if o.strip()
        ),
    )
