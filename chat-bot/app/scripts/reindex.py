from __future__ import annotations

from app.api.dependencies import get_sync_service


def main() -> None:
    indexed = get_sync_service().run_full_sync()
    print(f"Indexed {indexed} FAQs")


if __name__ == "__main__":
    main()

