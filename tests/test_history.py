from pathlib import Path

from rawpilot.history import HistoryStore
from rawpilot.models import Diagnosis, ProcessResult


def test_project_history_round_trip(tmp_path: Path):
    store = HistoryStore(tmp_path / "history.json")
    source = tmp_path / "frame.NEF"
    source.touch()
    project = store.begin(tmp_path / "output", [source])
    result = ProcessResult(
        source=source,
        status="成功",
        diagnosis=Diagnosis(summary="夜景曝光不足", suggested_style="提亮人物，压暗天空"),
        suggested_style="提亮人物，压暗天空",
        final_prompt="天空转为黑灰，保留人物暗部",
        xmp_path=tmp_path / "output" / "frame.xmp",
    )
    store.record(project.id, result, result.final_prompt)

    loaded = store.load()
    assert loaded[0].title == "frame"
    assert loaded[0].items[0].source == str(source)
    assert loaded[0].items[0].final_prompt == "天空转为黑灰，保留人物暗部"
    assert loaded[0].items[0].diagnosis["summary"] == "夜景曝光不足"


def test_project_history_replaces_same_source(tmp_path: Path):
    store = HistoryStore(tmp_path / "history.json")
    source = tmp_path / "frame.DNG"
    project = store.begin(tmp_path / "output", [source])
    store.record(project.id, ProcessResult(source=source, status="失败"), "第一次")
    store.record(project.id, ProcessResult(source=source, status="成功"), "第二次")

    items = store.load()[0].items
    assert len(items) == 1
    assert items[0].status == "成功"
    assert items[0].final_prompt == "第二次"


def test_project_can_use_revision_title(tmp_path: Path):
    source = tmp_path / "frame.NEF"
    project = HistoryStore(tmp_path / "history.json").begin(
        tmp_path / "output",
        [source],
        title="frame · 后处理",
    )
    assert project.title == "frame · 后处理"
