"""Bridge to claude-grid tmux sessions."""

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class SessionInfo:
    """Information about a claude-grid tmux session."""
    name: str        # e.g. "aspen-ember"
    full_name: str   # e.g. "cg/aspen-ember"
    words: list[str] # e.g. ["aspen", "ember"]


class ClaudeGridBridge:
    """Interface for discovering and sending text to claude-grid tmux sessions."""

    CG_PREFIX = "cg/"

    def is_available(self) -> bool:
        """Check if tmux is installed and accessible."""
        return shutil.which("tmux") is not None

    def discover_sessions(self) -> list[SessionInfo]:
        """Discover active claude-grid sessions.

        Returns a list of SessionInfo for sessions matching the cg/* pattern.
        """
        if not self.is_available():
            return []

        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return []

            sessions = []
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if line.startswith(self.CG_PREFIX):
                    name = line[len(self.CG_PREFIX):]
                    if name:
                        sessions.append(SessionInfo(
                            name=name,
                            full_name=line,
                            words=name.split("-"),
                        ))
            return sessions

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return []

    def send_text(self, session_name: str, text: str) -> bool:
        """Send literal text to a claude-grid session.

        Uses tmux send-keys with -l flag to send text literally,
        preventing tmux from interpreting words like "Enter" as key names.

        Returns True on success.
        """
        target = f"{self.CG_PREFIX}{session_name}"
        try:
            result = subprocess.run(
                ["tmux", "send-keys", "-l", "-t", target, text],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def send_enter(self, session_name: str) -> bool:
        """Send Enter key to a claude-grid session.

        Returns True on success.
        """
        target = f"{self.CG_PREFIX}{session_name}"
        try:
            result = subprocess.run(
                ["tmux", "send-keys", "-t", target, "Enter"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def focus_grid_pane(self, session_name: str) -> bool:
        """Focus the pane for a session in the cg-grid window.

        Finds the pane index in the cg-grid session and selects it.
        Returns True on success.
        """
        try:
            # List panes in cg-grid, find the one with matching session title
            result = subprocess.run(
                ["tmux", "list-panes", "-t", "cg-grid", "-F",
                 "#{pane_index}:#{pane_title}"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return False

            for line in result.stdout.strip().splitlines():
                if session_name in line:
                    pane_index = line.split(":")[0]
                    select_result = subprocess.run(
                        ["tmux", "select-pane", "-t",
                         f"cg-grid:{pane_index}"],
                        capture_output=True, text=True, timeout=5,
                    )
                    return select_result.returncode == 0

            return False
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
