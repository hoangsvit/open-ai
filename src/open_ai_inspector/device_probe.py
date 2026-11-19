"""Read-only ADB package inspection, without root, Frida, or billing access."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import shutil
import subprocess
from typing import Callable

CHATGPT_PACKAGE = "com.openai.chatgpt"
_STATES = {"device", "unauthorized", "offline", "recovery", "sideload", "bootloader"}


@dataclass(frozen=True)
class DeviceResult:
    state: str
    message: str
    device_count: int = 0
    installed: bool | None = None
    version: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def _adb(executable: str, args: list[str], runner: Callable) -> str:
    outcome = runner(
        [executable, *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=10, check=False,
    )
    if outcome.returncode != 0:
        raise RuntimeError("ADB command failed")
    return outcome.stdout or ""


def _parse_devices(stdout: str) -> dict[str, str]:
    found = {}
    for line in stdout.splitlines():
        fields = line.strip().split()
        if len(fields) >= 2 and fields[1] in _STATES:
            found[fields[0]] = fields[1]
    return found


def probe_android(
    adb: str | None = None,
    serial: str | None = None,
    runner: Callable | None = None,
) -> DeviceResult:
    """Only ADB devices, pm path, and dumpsys package are run."""
    binary = adb or shutil.which("adb")
    if not binary:
        return DeviceResult("adb_missing", "ADB not found. Install Android Platform-Tools.")
    run = runner or subprocess.run
    try:
        devices = _parse_devices(_adb(binary, ["devices"], run))
        count = len(devices)
        if not count:
            return DeviceResult("device_missing", "No connected Android device.", 0)
        if serial:
            if serial not in devices:
                return DeviceResult("device_not_found", "Selected device not found.", count)
            selected = serial
        else:
            if count != 1:
                return DeviceResult(
                    "multiple_devices",
                    "Multiple devices detected. Choose one via --serial.", count,
                )
            selected = next(iter(devices))
        if devices[selected] != "device":
            return DeviceResult(
                devices[selected], "Android is not ready; check ADB connection.", count,
            )
        cmd = ["-s", selected, "shell"]
        output = _adb(binary, cmd + ["pm", "path", CHATGPT_PACKAGE], run)
        installed = any(line.strip().startswith("package:") for line in output.splitlines())
        if not installed:
            return DeviceResult("app_missing", "ChatGPT Android app not installed.", count, False)
        details = _adb(binary, cmd + ["dumpsys", "package", CHATGPT_PACKAGE], run)
        match = re.search(r"(?m)^\s*versionName=([^\s]+)", details)
        version = match.group(1) if match else None
        if version and not re.fullmatch(r"[A-Za-z0-9._+-]{1,64}", version):
            version = None
        return DeviceResult(
            "detected", "ChatGPT app detected; subscription not verified.",
            count, True, version,
        )
    except (OSError, subprocess.TimeoutExpired, RuntimeError):
        return DeviceResult("adb_error", "ADB failed or timed out.")
