from __future__ import annotations

from desktop_launcher.browser_opener import open_dashboard
from desktop_launcher.launcher_config import DEFAULT_DASHBOARD_URL


def main() -> None:
    open_dashboard(DEFAULT_DASHBOARD_URL)


if __name__ == "__main__":
    main()
