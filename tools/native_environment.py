"""Reject native attack runs when the console session cannot supply valid controls."""

import plistlib
import subprocess


class NativeEnvironmentUnavailable(RuntimeError):
    pass


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


def require_unlocked():
    try:
        raw = subprocess.check_output(["/usr/sbin/ioreg", "-n", "Root", "-d", "1", "-a"], timeout=5)
        state = console_state(plistlib.loads(raw))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise NativeEnvironmentUnavailable("Cannot establish an unlocked native session") from error
    if state["locked"] is not False:
        raise NativeEnvironmentUnavailable("Unlock the Mac manually before native trials. No prevention result is valid while locked.")
    return state
