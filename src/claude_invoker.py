import sys
import subprocess
from constants import SKILL_PATH, MAX_FIX_ATTEMPTS
from notifications import notify


def trigger_claude_fix(
    action_name: str | None,
    sqlx_path: str | None,
    error_msg: str,
    branch: str,
    wt_path: str,
):
    try:
        with open(SKILL_PATH) as f:
            system_prompt = f.read()
    except OSError as exc:
        print(f"[scout] Cannot read skill file {SKILL_PATH}: {exc}", file=sys.stderr)
        return

    prompt_lines = [
        f"Branch: {branch}",
        f"Error: {error_msg}",
    ]
    if action_name:
        prompt_lines.insert(0, f"Action: {action_name}")
    if sqlx_path:
        prompt_lines.insert(0, f"File: {sqlx_path}")

    prompt = "\n".join(prompt_lines)

    for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
        print(f"[scout] Claude fix attempt {attempt}/{MAX_FIX_ATTEMPTS}...")
        try:
            subprocess.run(
                [
                    "claude",
                    "--system-prompt",
                    system_prompt,
                    "--permission-mode",
                    "auto",
                    "-p",
                    prompt,
                ],
                text=True,
                timeout=120,
                cwd=wt_path,
            )

            compile_res = subprocess.run(
                ["dataform", "compile"], cwd=wt_path, capture_output=True, text=True
            )
            if compile_res.returncode == 0:
                print(f"[scout] Fix successful on attempt {attempt}.")
                notify(
                    "Dataform Scout",
                    "Fix successful!",
                    f"Compiled successfully on attempt {attempt}",
                )
                return
            else:
                prompt = f"The previous fix did not resolve the error. Dataform compile output:\n{compile_res.stderr}\nPlease try again."
        except FileNotFoundError:
            print("[scout] WARNING: `claude` CLI not found.", file=sys.stderr)
            return
        except subprocess.TimeoutExpired:
            print(
                f"[scout] WARNING: claude fix attempt {attempt} timed out after 120s.",
                file=sys.stderr,
            )
            prompt = "The previous fix attempt timed out. Please be more concise and try again."

    print(f"[scout] Failed to fix after {MAX_FIX_ATTEMPTS} attempts. Reverting.")
    subprocess.run(["git", "checkout", "."], cwd=wt_path)
    subprocess.run(["git", "checkout", "-"], cwd=wt_path)
    subprocess.run(["git", "branch", "-D", branch], cwd=wt_path)
    notify(
        "Dataform Scout",
        "Auto-fix failed",
        f"Could not fix after {MAX_FIX_ATTEMPTS} attempts. Reverted changes.",
    )
