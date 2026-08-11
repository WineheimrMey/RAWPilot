from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from .analyzer import analyze, review_render
from .api_client import QwenApiClient
from .lightroom_bridge import LightroomBridge
from .models import ProcessResult
from .planner import plan_edits, refine_edits
from .preview import prepare_local_asset
from .quality import assess_render, recover_underexposed_plan
from .settings import AppSettings
from .xmp_writer import write_xmp

log = logging.getLogger("rawpilot")


class WorkerSignals(QObject):
    item_done = Signal(int, object)
    item_status = Signal(int, str)
    finished = Signal()


class PreflightWorker(QRunnable):
    def __init__(self, files: list[Path], settings: AppSettings):
        super().__init__()
        self.files, self.settings = files, settings
        self.signals = WorkerSignals()

    def run(self) -> None:
        client = QwenApiClient(self.settings)
        for index, path in enumerate(self.files):
            result = ProcessResult(source=path, status="分析中")
            self.signals.item_status.emit(index, "分析中")
            try:
                asset = prepare_local_asset(path)
                diagnosis = analyze(asset, client, self.settings.mock_mode)
                result.preview_path = asset.preview_path
                result.diagnosis = diagnosis
                result.suggested_style = diagnosis.suggested_style
                result.status = "待确认"
            except Exception as exc:
                result.status, result.error = "失败", str(exc)
                log.exception("预分析失败 %s", path.name)
            self.signals.item_done.emit(index, result)
        self.signals.finished.emit()


class BatchWorker(QRunnable):
    def __init__(
        self,
        files: list[Path],
        output_dir: Path,
        styles: dict[str, str],
        settings: AppSettings,
        prepared: dict[str, ProcessResult] | None = None,
    ):
        super().__init__()
        self.files, self.output_dir, self.styles, self.settings = files, output_dir, styles, settings
        self.prepared = prepared or {}
        self.signals = WorkerSignals()

    def run(self) -> None:
        client = QwenApiClient(self.settings)
        for index, path in enumerate(self.files):
            cached = self.prepared.get(str(path))
            result = ProcessResult(
                source=path,
                status="处理中",
                preview_path=cached.preview_path if cached else None,
                diagnosis=cached.diagnosis if cached else None,
                suggested_style=cached.suggested_style if cached else "",
            )
            asset = None
            self.signals.item_status.emit(index, "处理中")
            try:
                if cached and cached.diagnosis:
                    diagnosis = cached.diagnosis
                    preview_path = cached.preview_path
                    suggestion = cached.suggested_style
                else:
                    asset = prepare_local_asset(path)
                    diagnosis = analyze(asset, client, self.settings.mock_mode)
                    preview_path = asset.preview_path
                    suggestion = diagnosis.suggested_style
                style = self.styles.get(str(path)) or suggestion or "自然真实"
                plan = plan_edits(diagnosis, style, client, self.settings.mock_mode)
                xmp_path, _ = write_xmp(path, plan, self.output_dir)
                result.preview_path = preview_path
                result.diagnosis = diagnosis
                result.suggested_style = suggestion
                result.final_prompt = style
                result.plan = plan
                result.xmp_path = xmp_path
                if self.settings.lightroom_enabled:
                    bridge = LightroomBridge(self.settings.lightroom_path)
                    result.rendered_path = bridge.render(path, plan, self.output_dir)
                    if preview_path:
                        report = assess_render(preview_path, result.rendered_path, style)
                        result.quality_note = report.summary
                        log.info("%s %s", path.name, report.summary)
                        if not report.passed:
                            recovered = recover_underexposed_plan(plan, report, style)
                            result.plan = recovered
                            result.xmp_path, _ = write_xmp(
                                path, recovered, self.output_dir
                            )
                            # The first pass already created the requested masks.
                            # Reapply only recovered global settings so a retry
                            # cannot stack duplicate AI masks in the catalog.
                            result.rendered_path = bridge.render(
                                path,
                                recovered,
                                self.output_dir,
                                replace_existing_masks=True,
                            )
                            second = assess_render(
                                preview_path, result.rendered_path, style
                            )
                            result.quality_note = (
                                report.summary + "\n自动恢复后：" + second.summary
                            )
                            if not second.passed:
                                raise RuntimeError(
                                    "成片自动恢复后仍未通过亮度质检；已保留输出供检查，"
                                    "但不会把这张照片标记为成功。"
                                )
                    if not self.settings.mock_mode and result.rendered_path:
                        try:
                            review_plan = result.plan or plan
                            for review_index in range(3):
                                review = review_render(
                                    preview_path or result.rendered_path,
                                    result.rendered_path,
                                    style,
                                    review_plan,
                                    client,
                                )
                                result.quality_note = (
                                    (
                                        result.quality_note + "\n"
                                    ) if result.quality_note else ""
                                ) + (
                                    f"第 {review_index + 1} 次"
                                    + review.summary
                                )
                                if not review.retry_required:
                                    break
                                if (
                                    review_index >= 2
                                    or not review.feedback.strip()
                                ):
                                    raise RuntimeError(
                                        "成片经过两次自动返工后仍未通过双图复审；"
                                        "已保留最后版本，但不会标记为成功。"
                                    )
                                review_plan = refine_edits(
                                    diagnosis,
                                    review_plan,
                                    style,
                                    "成片自动复审意见：" + review.feedback,
                                    client,
                                )
                                result.plan = review_plan
                                result.xmp_path, _ = write_xmp(
                                    path, review_plan, self.output_dir
                                )
                                result.rendered_path = bridge.render(
                                    path,
                                    review_plan,
                                    self.output_dir,
                                    replace_existing_masks=True,
                                )
                                final_report = (
                                    assess_render(
                                        preview_path,
                                        result.rendered_path,
                                        style,
                                    )
                                    if preview_path else None
                                )
                                result.quality_note += (
                                    f"\n已按第 {review_index + 1} 次复审意见自动返工。"
                                    + (
                                        "\n返工后：" + final_report.summary
                                        if final_report else ""
                                    )
                                )
                                if final_report and not final_report.passed:
                                    raise RuntimeError(
                                        "AI 自动返工后亮度质检未通过，已保留该版本供检查。"
                                    )
                        except RuntimeError:
                            raise
                        except Exception as review_error:
                            log.warning(
                                "成片视觉复审跳过 %s: %s",
                                path.name,
                                review_error,
                            )
                            result.quality_note += (
                                "\nAI 成片复审暂不可用，已保留通过基础质检的版本。"
                            )
                result.status = "成功"
                log.info("完成 %s -> %s", path.name, xmp_path)
            except Exception as exc:
                result.status, result.error = "失败", str(exc)
                if asset is not None:
                    result.preview_path = asset.preview_path
                log.exception("处理失败 %s", path.name)
            self.signals.item_done.emit(index, result)
        self.signals.finished.emit()


class RefineWorker(QRunnable):
    def __init__(
        self,
        current: ProcessResult,
        output_dir: Path,
        feedback: str,
        settings: AppSettings,
    ):
        super().__init__()
        self.current = current
        self.output_dir = output_dir
        self.feedback = feedback
        self.settings = settings
        self.signals = WorkerSignals()

    def run(self) -> None:
        result = self.current.model_copy(deep=True)
        result.status = "处理中"
        result.error = ""
        self.signals.item_status.emit(0, "处理中")
        try:
            if not result.diagnosis or not result.plan:
                raise ValueError("当前照片缺少第一版诊断或参数，无法进行后处理。")
            client = QwenApiClient(self.settings)
            original_intent = result.final_prompt or result.suggested_style
            revised = refine_edits(
                result.diagnosis,
                result.plan,
                original_intent,
                self.feedback,
                client,
                self.settings.mock_mode,
            )
            revision = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            revision_dir = (
                self.output_dir
                / "revisions"
                / f"{result.source.stem}_{revision}"
            )
            result.plan = revised
            result.final_prompt = (
                original_intent + "\n\n【后处理意见】" + self.feedback.strip()
            )
            result.xmp_path, _ = write_xmp(
                result.source, revised, revision_dir
            )
            if self.settings.lightroom_enabled:
                bridge = LightroomBridge(self.settings.lightroom_path)
                result.rendered_path = bridge.render(
                    result.source,
                    revised,
                    revision_dir,
                    replace_existing_masks=True,
                )
                if result.preview_path:
                    report = assess_render(
                        result.preview_path,
                        result.rendered_path,
                        result.final_prompt,
                    )
                    result.quality_note = report.summary
                    if not report.passed:
                        recovered = recover_underexposed_plan(
                            revised, report, result.final_prompt
                        )
                        result.plan = recovered
                        result.xmp_path, _ = write_xmp(
                            result.source, recovered, revision_dir
                        )
                        result.rendered_path = bridge.render(
                            result.source,
                            recovered,
                            revision_dir,
                            replace_existing_masks=True,
                        )
                        second = assess_render(
                            result.preview_path,
                            result.rendered_path,
                            result.final_prompt,
                        )
                        result.quality_note += "\n自动恢复后：" + second.summary
                        if not second.passed:
                            raise RuntimeError(
                                "后处理成片仍未通过亮度质检，已保留该版本供检查。"
                            )
                if not self.settings.mock_mode and result.rendered_path:
                    try:
                        review = review_render(
                            result.preview_path or result.rendered_path,
                            result.rendered_path,
                            result.final_prompt,
                            result.plan,
                            client,
                        )
                        result.quality_note += "\n" + review.summary
                    except Exception as review_error:
                        log.warning(
                            "后处理视觉复审跳过 %s: %s",
                            result.source.name,
                            review_error,
                        )
            result.status = "成功"
            log.info("后处理完成 %s -> %s", result.source.name, revision_dir)
        except Exception as exc:
            result.status, result.error = "失败", str(exc)
            log.exception("后处理失败 %s", result.source.name)
        self.signals.item_done.emit(0, result)
        self.signals.finished.emit()


class TaskManager:
    def __init__(self):
        self.pool = QThreadPool.globalInstance()
        self._active: BatchWorker | PreflightWorker | RefineWorker | None = None

    def analyze(self, files: list[Path], settings: AppSettings) -> PreflightWorker:
        worker = PreflightWorker(files, settings)
        self._active = worker
        self.pool.start(worker)
        return worker

    def start(
        self,
        files: list[Path],
        output_dir: Path,
        styles: dict[str, str],
        settings: AppSettings,
        prepared: dict[str, ProcessResult] | None = None,
    ) -> BatchWorker:
        worker = BatchWorker(files, output_dir, styles, settings, prepared)
        self._active = worker
        self.pool.start(worker)
        return worker

    def refine(
        self,
        current: ProcessResult,
        output_dir: Path,
        feedback: str,
        settings: AppSettings,
    ) -> RefineWorker:
        worker = RefineWorker(current, output_dir, feedback, settings)
        self._active = worker
        self.pool.start(worker)
        return worker
