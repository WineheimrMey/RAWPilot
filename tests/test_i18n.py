from rawpilot.i18n import normalize_language, output_language_instruction, tr


def test_ui_translation_and_formatting() -> None:
    assert tr("工作台", "en_US") == "Studio"
    assert tr("模型服务已响应：{reply}", "en_US", reply="OK") == "Model service responded: OK"
    assert tr("工作台", "zh_CN") == "工作台"


def test_language_is_bounded_and_drives_agent_output() -> None:
    assert normalize_language("fr_FR") == "zh_CN"
    assert "professional English" in output_language_instruction("en_US")
    assert "专业的中文" in output_language_instruction("zh_CN")
