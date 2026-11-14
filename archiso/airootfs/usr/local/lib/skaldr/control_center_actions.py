#!/usr/bin/env python3
"""Pure, independently testable action policy for Skaldr Control Center.

No command executes during import, and no UI is required to run the tests.
Every state-changing operation needs an explicit user decision in the GUI.
"""
from pathlib import Path
import shutil

READ_ONLY = {
    "health": ["/usr/local/bin/skaldr-doctor", "--json"],
    "graphics": ["/usr/local/bin/skaldr-gpu-diagnostics"],
    "recovery": ["/usr/local/bin/skaldr-recovery"],
    "version": ["/usr/local/bin/skaldr-version", "--json"],
}
EXTERNAL_TOOLS = {
    "systemsettings": ["systemsettings"],
    "gpu_assistant": ["/usr/local/bin/skaldr-gpu-assistant", "--recheck"],
    "snapshots": ["btrfs-assistant"],
    "virtual_machines": ["virt-manager"],
    "gpu_tuning": ["lact", "gui"],
}
PROFILE_CHOICES = ("balanced", "gaming", "creator")
REPORT_EXECUTABLE = "/usr/local/bin/skaldr-report"
UPDATE_EXECUTABLE = "/usr/local/bin/skaldr-update"
PROFILE_EXECUTABLE = "/usr/local/bin/skaldr-performance"


def power_mode_command(mode, approved=False):
    """Return a terminal+polkit command only after explicit approval."""
    if mode not in PROFILE_CHOICES:
        raise ValueError("Unsupported power mode")
    if not approved:
        raise PermissionError("Power profile change requires consent")
    return ["konsole", "--hold", "-e", "pkexec",
            PROFILE_EXECUTABLE, "apply", mode, "--confirm"]


def update_command(root_fs, approved=False):
    """Do not allow unprotected ext4/XFS upgrades through the GUI."""
    if root_fs != "btrfs":
        raise ValueError(
            "Only Btrfs root with a working Snapper profile can be "
            "updated through the Control Center. The terminal-only "
            "--allow-without-snapshot escape hatch is not exposed here."
        )
    if not approved:
        raise PermissionError("System update requires consent")
    return ["konsole", "--hold", "-e", "pkexec", UPDATE_EXECUTABLE, "--apply"]


def report_command(destination):
    """Local-only diagnostic export; never overwrite an existing file."""
    path = Path(destination).expanduser()
    if not path.is_absolute():
        raise ValueError("Choose an absolute local path")
    if path.exists() or path.is_symlink():
        raise FileExistsError("Destination already exists")
    if not path.parent.is_dir():
        raise FileNotFoundError("Destination directory does not exist")
    return [REPORT_EXECUTABLE, "--write", str(path)]


def get_external_tool(key):
    if key not in EXTERNAL_TOOLS:
        raise KeyError("Unknown tool")
    program, *args = EXTERNAL_TOOLS[key]
    if not Path(program).is_absolute() and shutil.which(program) is None:
        raise FileNotFoundError(f"{program} is not installed")
    if Path(program).is_absolute() and not Path(program).is_file():
        raise FileNotFoundError(f"{program} is not installed")
    return [program, *args]


def display_value(value):
    if value is True:
        return "Enabled"
    if value is False:
        return "Disabled"
    if value is None:
        return "Not detected"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "None"
    if isinstance(value, dict):
        return ", ".join(f"{key}: {display_value(item)}" for key, item in value.items())
    return str(value)
