"""Record console metadata without treating it as proof that an attack route works."""

import plistlib
import subprocess


def console_state(registry):
    nodes = registry if isinstance(registry, list) else [registry]
    sessions = [session for node in nodes for session in node.get("IOConsoleUsers", [])
                if session.get("kCGSessionLoginDoneKey") is True]
    if len(sessions) != 1:
        return {"locked": None, "reason": "No unique logged-in console session"}
    locked = sessions[0].get("CGSSessionScreenIsLocked")
    if not isinstance(locked, bool):
        return {"locked": None, "reason": "Console lock flag unavailable"}
    return {"locked": locked}


def observe_console():
    try:
        raw = subprocess.check_output(["/usr/sbin/ioreg", "-n", "Root", "-d", "1", "-a"], timeout=5)
        state = console_state(plistlib.loads(raw))
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"locked": None, "reason": "Console observation unavailable", "advisory": True}
    state["advisory"] = True
    return state


def action_verdict(completed, refused, control_worked):
    if completed:
        return "bypass"
    if refused and control_worked:
        return "blocked"
    return "inconclusive"
