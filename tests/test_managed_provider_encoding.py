from node_agent.managed_provider import repair_mojibake


def test_repair_mojibake_keeps_normal_text():
    text = "正在连接实时终端...\r\n[AgentDeck live terminal connected]\r\n"
    assert repair_mojibake(text) == text


def test_repair_mojibake_fixes_common_windows_console_text():
    text = "正在连接"
    mojibake = text.encode("utf-8").decode("gbk", errors="replace")
    assert repair_mojibake(mojibake) == text


def test_repair_mojibake_keeps_already_damaged_text():
    damaged = "AgentDeck 鎺у埗鍙�"
    assert repair_mojibake(damaged) == damaged
