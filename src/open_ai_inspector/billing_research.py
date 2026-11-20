"""Passive research of ChatGPT's possible Android Play Billing integration.

Only read-only ADB package inspection is run by default. An *explicit* --runtime
request may attach to a running app and enumerate a fixed set of loaded Java
class names. Neither mode queries products/offers, intercepts calls, reads tokens,
makes purchases or verifies subscriptions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import resources
import shutil
import subprocess
from threading import Event
from typing import Callable

from .device_probe import CHATGPT_PACKAGE, _adb, _parse_devices, probe_android

PLAY_STORE_PACKAGE = "com.android.vending"
FRIDA_VERSION = "16.5.9"
BILLING_CLASSES = (
    "com.android.billingclient.api.BillingClient",
    "com.android.billingclient.api.BillingClientImpl",
    "com.android.billingclient.api.ProductDetails",
    "com.android.billingclient.api.BillingFlowParams",
    "com.android.billingclient.api.PurchasesUpdatedListener",
)


@dataclass(frozen=True)
class BillingProbeResult:
    state: str
    message: str
    app_installed: bool | None = None
    app_version: str | None = None
    play_store_installed: bool | None = None
    runtime_status: str = "not_requested"
    billing_classes_loaded: tuple[str, ...] = ()
    billing_library_loaded: bool | None = None
    eligibility_verified: bool = False
    subscription_verified: bool = False
    checkout_attempted: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def _class_probe(frida_module, frida_device_id: str | None, timeout: int = 15):
    """One-shot class-name enumeration. Never hook methods or inspect objects."""
    version = getattr(frida_module, "__version__", "")
    if version != FRIDA_VERSION:
        return "unsupported_frida", (), "Requires Frida 16.5.9 with the bundled Java bridge."
    script_source = resources.files("open_ai_inspector").joinpath(
        "data/billing_class_probe.js"
    ).read_text(encoding="utf-8")
    done = Event()
    data: dict = {}
    session = None
    script = None

    def on_message(message, _binary_data):
        # Do not serialize raw Frida messages; they can contain app internals.
        if not isinstance(message, dict):
            return
        if message.get("type") == "error":
            data["status"] = "agent_error"
            done.set()
            return
        if message.get("type") != "send":
            return
        payload = message.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "billing_class_probe":
            return
        if payload.get("java_available") is not True:
            data["status"] = "java_unavailable"
            done.set()
            return
        names = payload.get("loaded_classes")
        if not isinstance(names, list) or len(names) > len(BILLING_CLASSES):
            data["status"] = "invalid_agent_result"
            done.set()
            return
        if not all(isinstance(name, str) and name in BILLING_CLASSES for name in names):
            data["status"] = "invalid_agent_result"
            done.set()
            return
        data["status"] = "complete"
        data["classes"] = tuple(sorted(set(names)))
        done.set()

    try:
        if frida_device_id:
            device = frida_module.get_device(frida_device_id, timeout=5)
        else:
            device = frida_module.get_usb_device(timeout=5)
        # Attach only. Never spawn, resume, kill, install or start a payment flow.
        session = device.attach(CHATGPT_PACKAGE)
        script = session.create_script(script_source)
        script.on("message", on_message)
        script.load()
        if not done.wait(timeout):
            return "timeout", (), "Passive runtime scan timed out; result is unknown."
        status = data.get("status", "invalid_agent_result")
        if status == "complete":
            return status, data.get("classes", ()), "Observed loaded billing class names."
        if status == "java_unavailable":
            return status, (), "Android Java runtime was unavailable at the time of inspection."
        return status, (), "Runtime inspection failed; no billing result was accepted."
    except Exception:
        # Do not echo raw exceptions: they may contain process/device identifiers.
        return "attach_failed", (), "Unable to attach to the running ChatGPT process."
    finally:
        if script is not None:
            try:
                script.unload()
            except Exception:
                pass
        if session is not None:
            try:
                session.detach()
            except Exception:
                pass


def inspect_billing(
    *,
    adb: str | None = None,
    serial: str | None = None,
    runtime: bool = False,
    frida_device_id: str | None = None,
    frida_module=None,
    runner: Callable | None = None,
) -> BillingProbeResult:
    """Inspect a selected Android device without credentials or payment operations.

    If more than one Android device is connected, runtime attach requires both
    an explicit ADB serial and an explicit Frida device ID to avoid ambiguity.
    """
    app = probe_android(adb=adb, serial=serial, runner=runner)
    if app.state != "detected":
        return BillingProbeResult(
            app.state, app.message, app.installed, app.version,
            runtime_status="not_attempted" if runtime else "not_requested",
        )
    binary = adb or shutil.which("adb")
    run = runner or subprocess.run
    try:
        devices = _parse_devices(_adb(binary, ["devices"], run))
        selected = serial or (next(iter(devices)) if len(devices) == 1 else None)
        if selected is None or devices.get(selected) != "device":
            return BillingProbeResult(
                "device_selection_required", "Select an authorized Android device.",
                True, app.version,
            )
        output = _adb(binary, ["-s", selected, "shell", "pm", "path", PLAY_STORE_PACKAGE], run)
        play_installed = any(
            line.strip().startswith("package:") for line in output.splitlines()
        )
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        play_installed = None
    if not runtime:
        return BillingProbeResult(
            "inspected", "Read-only package inspection complete; billing integration unknown.",
            True, app.version, play_installed,
        )
    if app.device_count > 1 and (not serial or not frida_device_id):
        return BillingProbeResult(
            "inspected",
            "Multiple devices: both --serial and --frida-device-id are required for runtime scan.",
            True, app.version, play_installed, "device_selection_required",
        )
    if frida_module is None:
        try:
            import frida as frida_module
        except ImportError:
            return BillingProbeResult(
                "inspected", "Optional Frida is not installed; runtime check skipped.",
                True, app.version, play_installed, "frida_missing",
            )
    status, names, message = _class_probe(frida_module, frida_device_id)
    # A loaded class is not a product/offer or proof an account is eligible.
    loaded = any(name.endswith(".BillingClient") for name in names) if status == "complete" else None
    return BillingProbeResult(
        "inspected", message, True, app.version, play_installed,
        status, names, loaded,
    )
