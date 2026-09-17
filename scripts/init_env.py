"""Create private local configuration; never rotate credentials for existing volumes."""

import os
import secrets
from pathlib import Path


def main():
    path = Path(".env")
    if path.exists():
        raise SystemExit(".env already exists; preserved.")
    template = Path(".env.example").read_text()
    for name in ("MINIO_ROOT_PASSWORD", "POSTGRES_PASSWORD"):
        lines = template.splitlines()
        template = (
            "\n".join(
                f"{name}={secrets.token_urlsafe(32)}" if line.startswith(f"{name}=") else line
                for line in lines
            )
            + "\n"
        )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        handle.write(template)
    print("Created private .env with random local credentials.")


if __name__ == "__main__":
    main()
