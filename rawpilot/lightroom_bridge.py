from __future__ import annotations

import os
import hashlib
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from .models import EditPlan

BRIDGE_VERSION = "0.5"

LIGHTROOM_COMMON_PATHS = (
    Path(r"D:\Program Files (x86)\Lightroom\Adobe Lightroom Classic\Lightroom.exe"),
    Path(r"C:\Program Files\Adobe\Adobe Lightroom Classic\Lightroom.exe"),
    Path(r"C:\Program Files\Adobe\Adobe Lightroom Classic\Adobe Lightroom Classic.exe"),
)

COLOR_NAMES = {
    "red": "Red", "orange": "Orange", "yellow": "Yellow", "green": "Green",
    "aqua": "Aqua", "blue": "Blue", "purple": "Purple", "magenta": "Magenta",
}

LOCAL_FIELDS = {
    "exposure": "local_Exposure",
    "contrast": "local_Contrast",
    "highlights": "local_Highlights",
    "shadows": "local_Shadows",
    "whites": "local_Whites",
    "blacks": "local_Blacks",
    "texture": "local_Texture",
    "clarity": "local_Clarity",
    "dehaze": "local_Dehaze",
    "saturation": "local_Saturation",
    "temperature": "local_Temperature",
    "tint": "local_Tint",
    "luminance_noise_reduction": "local_LuminanceNoise",
}


class LightroomError(RuntimeError):
    pass


def detect_lightroom() -> Path | None:
    for candidate in LIGHTROOM_COMMON_PATHS:
        if candidate.exists():
            return candidate
    if sys.platform == "win32":
        try:
            import winreg
            registry_paths = (
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            )
            for registry_path in registry_paths:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as root:
                    for index in range(winreg.QueryInfoKey(root)[0]):
                        with winreg.OpenKey(root, winreg.EnumKey(root, index)) as item:
                            try:
                                name = str(winreg.QueryValueEx(item, "DisplayName")[0])
                                location = Path(str(winreg.QueryValueEx(item, "InstallLocation")[0]))
                            except OSError:
                                continue
                            if name == "Adobe Lightroom Classic":
                                candidate = location / "Adobe Lightroom Classic" / "Lightroom.exe"
                                if candidate.exists():
                                    return candidate
        except OSError:
            pass
    return None


def plugin_install_dir() -> Path:
    appdata = Path(os.environ.get("APPDATA") or Path.home())
    return appdata / "Adobe" / "Lightroom" / "Modules" / "RAWPilot.lrplugin"


def queue_dir() -> Path:
    appdata = Path(os.environ.get("APPDATA") or Path.home())
    return appdata / "RAWPilot" / "lightroom_queue"


def bundled_plugin_dir() -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return root / "lightroom_plugin" / "RAWPilot.lrplugin"


class LightroomBridge:
    def __init__(self, executable: str | Path = ""):
        self.executable = Path(executable) if executable else detect_lightroom()
        self.bridge_mode = "unknown"

    def install_plugin(self) -> Path:
        source = bundled_plugin_dir()
        if not source.exists():
            raise LightroomError(f"缺少内置 Lightroom Bridge：{source}")
        target = plugin_install_dir()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, dirs_exist_ok=True)
        qdir = queue_dir()
        qdir.mkdir(parents=True, exist_ok=True)
        (target / "queue_path.txt").write_text(str(qdir.resolve()), encoding="utf-8")
        return target

    def launch(self) -> None:
        if not self.executable or not self.executable.exists():
            raise LightroomError("未找到 Adobe Lightroom Classic，请在连接设置中指定 Lightroom.exe。")
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(
            [str(self.executable)],
            cwd=str(self.executable.parent),
            creationflags=creationflags,
            close_fds=True,
        )

    def render(
        self,
        raw_path: Path,
        plan: EditPlan,
        output_dir: Path,
        timeout: int = 300,
        replace_existing_masks: bool = False,
    ) -> Path:
        self.install_plugin()
        output_dir.mkdir(parents=True, exist_ok=True)
        qdir = queue_dir()
        self.launch()
        self.bridge_mode = self._wait_for_ready(qdir, timeout=35)
        job_id = uuid.uuid4().hex
        temp_path = qdir / f"{job_id}.tmp"
        job_path = qdir / f"{job_id}.job"
        status_path = qdir / f"{job_id}.status"

        values = plan.model_dump()
        lines = [
            str(raw_path.resolve()),
            str(output_dir.resolve()),
            raw_path.stem,
            "STATE|" + hashlib.sha1(
                str(raw_path.resolve()).lower().encode("utf-8")
            ).hexdigest(),
            f"WhiteBalance={values['white_balance']}",
            f"Exposure2012={values['exposure']}",
            f"Contrast2012={values['contrast']}",
            f"Highlights2012={values['highlights']}",
            f"Shadows2012={values['shadows']}",
            f"Whites2012={values['whites']}",
            f"Blacks2012={values['blacks']}",
            f"Texture={values['texture']}",
            f"Clarity2012={values['clarity']}",
            f"Dehaze={values['dehaze']}",
            f"Vibrance={values['vibrance']}",
            f"Saturation={values['saturation']}",
            f"Sharpness={values['sharpening']}",
            f"SharpenRadius={values['sharpening_radius']}",
            f"SharpenDetail={values['sharpening_detail']}",
            f"SharpenEdgeMasking={values['sharpening_masking']}",
            f"LuminanceSmoothing={values['luminance_noise_reduction']}",
            f"ColorNoiseReduction={values['color_noise_reduction']}",
            f"AutoLateralCA={1 if values['remove_chromatic_aberration'] else 0}",
            f"LensProfileEnable={1 if values['enable_profile_corrections'] else 0}",
        ]
        if values["white_balance"] == "Custom":
            lines.extend([
                f"Temperature={values['temperature']}",
                f"Tint={values['tint']}",
            ])
        for color, adobe_color in COLOR_NAMES.items():
            channel = values["color_mixer"][color]
            lines.extend([
                f"HueAdjustment{adobe_color}={channel['hue']}",
                f"SaturationAdjustment{adobe_color}={channel['saturation']}",
                f"LuminanceAdjustment{adobe_color}={channel['luminance']}",
            ])
        cinematic = values["cinematic"]
        lines.extend([
            f"ParametricShadows={cinematic['curve_shadows']}",
            f"ParametricDarks={cinematic['curve_darks']}",
            f"ParametricLights={cinematic['curve_lights']}",
            f"ParametricHighlights={cinematic['curve_highlights']}",
            f"SplitToningShadowHue={cinematic['shadow_hue']}",
            f"SplitToningShadowSaturation={cinematic['shadow_saturation']}",
            f"SplitToningHighlightHue={cinematic['highlight_hue']}",
            f"SplitToningHighlightSaturation={cinematic['highlight_saturation']}",
            f"SplitToningBalance={cinematic['split_balance']}",
            f"GrainAmount={cinematic['grain_amount']}",
            f"GrainSize={cinematic['grain_size']}",
            f"PostCropVignetteAmount={cinematic['vignette']}",
        ])
        mask_adjustments = values["local_adjustments"]
        if replace_existing_masks and self.bridge_mode == "legacy":
            # Legacy Bridge cannot identify masks it created earlier. Reusing
            # the catalog's existing masks is safer than stacking duplicates.
            mask_adjustments = []
        for adjustment in mask_adjustments:
            controls = [
                f"{adobe_name}:{adjustment[field]}"
                for field, adobe_name in LOCAL_FIELDS.items()
                if adjustment[field] != 0
            ]
            if controls:
                lines.append(f"MASK|{adjustment['target']}|" + ";".join(controls))
        temp_path.write_text("\n".join(lines), encoding="utf-8")
        temp_path.replace(job_path)

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if status_path.exists():
                status = status_path.read_text("utf-8", errors="replace").strip()
                try:
                    status_path.unlink()
                except OSError:
                    pass
                state, _, detail = status.partition("|")
                if state == "done":
                    rendered = Path(detail)
                    if rendered.exists():
                        return rendered
                    raise LightroomError(f"Lightroom 报告完成，但未找到导出文件：{rendered}")
                raise LightroomError("Lightroom 导出失败：" + detail)
            time.sleep(0.5)
        raise LightroomError(
            "Lightroom 已连接但任务执行超时。请查看日志：" + str(qdir / "bridge.log")
        )

    @staticmethod
    def _wait_for_ready(qdir: Path, timeout: int) -> str:
        ready = qdir / "bridge.ready"
        deadline = time.monotonic() + timeout
        legacy_seen = False
        while time.monotonic() < deadline:
            try:
                age = time.time() - ready.stat().st_mtime
                if age < 4:
                    handshake = ready.read_text(
                        "utf-8", errors="replace"
                    ).strip()
                    if handshake.startswith(f"ready|{BRIDGE_VERSION}|"):
                        return BRIDGE_VERSION
                    # A previous Bridge may still be resident in Lightroom
                    # after RAWPilot has replaced the plug-in files on disk.
                    # It remains usable for the current render; Lightroom will
                    # load the new Bridge on its next normal restart.
                    if handshake.startswith("ready|"):
                        legacy_seen = True
                        return "legacy"
            except OSError:
                pass
            time.sleep(0.5)
        raise LightroomError(
            f"Lightroom 已打开，但 RAWPilot Bridge {BRIDGE_VERSION} 没有握手。"
            + (
                "检测到旧版 Bridge 心跳但已经停止刷新。"
                if legacy_seen else ""
            )
            + "请完全退出并重新打开 "
            "Lightroom Classic，然后在“文件 → 增效工具管理器”确认插件来自："
            f"{plugin_install_dir()}。Bridge 日志：{qdir / 'bridge.log'}"
        )
