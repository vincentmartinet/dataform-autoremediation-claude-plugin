import subprocess


def notify(title: str, message: str, subtitle: str = "", sound: str = "Basso") -> None:
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
    subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True)
