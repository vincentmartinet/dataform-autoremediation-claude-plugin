"""Notifications module for sending macOS system alerts."""
import logging
import subprocess

logger = logging.getLogger(__name__)


def notify(title: str, message: str, subtitle: str = "", sound: str = "Basso") -> None:
    """Sends a system notification via macOS osascript."""
    safe_title = title.replace('"', "'")
    safe_message = message.replace('"', "'")
    safe_subtitle = subtitle.replace('"', "'")
    subtitle_clause = f' subtitle "{safe_subtitle}"' if safe_subtitle else ""
    sound_clause = f' sound name "{sound}"' if sound else ""
    script = (
        f'display notification "{safe_message}"'
        f' with title "{safe_title}"'
        f"{subtitle_clause}"
        f"{sound_clause}"
    )
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-e", script], capture_output=True, check=True
        )
    except subprocess.CalledProcessError as exc:
        logger.warning(
            f"Failed to send OS notification: {exc.stderr.decode('utf-8', errors='ignore')}"  # noqa: E501
        )
    except Exception as exc:
        logger.warning(f"Unexpected error while sending OS notification: {exc}")
