"""ContainerCraft tests. Daemon-dependent checks accept ok or down, never fail on absence."""

import json

from containercraft import cli


def test_down_when_no_engine(monkeypatch):
    monkeypatch.setattr(cli, "find_engine", lambda: None)
    st = cli.engine_status()
    assert st["status"] == "down" and st["available"] is False
    assert cli.ps()["containers"] == []
    assert cli.logs("x")["status"] == "down"
    assert cli.run_echo("hello-world", "hi")["status"] == "down"


def test_down_is_not_a_failure_exit(monkeypatch, capsys):
    monkeypatch.setattr(cli, "find_engine", lambda: None)
    assert cli.main(["status"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "down"


def test_json_lines_skips_noise():
    rows = cli._json_lines('{"a": 1}\nnot json\n{"b": 2}\n')
    assert rows == [{"a": 1}, {"b": 2}]


def test_ps_live_or_down():
    res = cli.ps()
    assert res["status"] in {"ok", "down"}
    if res["status"] == "ok":
        assert res["count"] == len(res["containers"])
        assert res["running"] <= res["count"]


def test_run_echo_never_pulls(monkeypatch):
    calls = []

    def fake_run(argv, timeout=60):
        calls.append(argv)

        class P:
            returncode = 1
            stdout = ""
            stderr = "no such image"

        return P()

    monkeypatch.setattr(cli, "engine_status", lambda: {"status": "ok", "engine": "docker"})
    monkeypatch.setattr(cli, "_run", fake_run)
    res = cli.run_echo("ghost:latest", "hi")
    assert res["status"] == "skipped"
    assert all("pull" not in a for a in calls) and len(calls) == 1


def test_cli_images(capsys):
    assert cli.main(["images"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] in {"ok", "down"}
