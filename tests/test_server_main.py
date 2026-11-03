"""The server binds to loopback unless network access is requested explicitly."""

from unittest.mock import patch

import pytest

server = pytest.importorskip("services.moza_server.main")


def _bound_host(argv, env=None):
    with patch.dict("os.environ", env or {}, clear=False), patch.object(server.uvicorn, "run") as run:
        server.main(argv)
    return run.call_args.kwargs["host"], run.call_args.kwargs["port"]


def test_defaults_to_loopback(monkeypatch):
    monkeypatch.delenv("MOZA_HOST", raising=False)
    monkeypatch.delenv("MOZA_PORT", raising=False)
    assert _bound_host([]) == ("127.0.0.1", 8100)


def test_env_opts_into_network_access():
    assert _bound_host([], {"MOZA_HOST": "0.0.0.0", "MOZA_PORT": "9000"}) == ("0.0.0.0", 9000)


def test_flags_override_env():
    assert _bound_host(["--host", "::1", "--port", "8200"], {"MOZA_HOST": "0.0.0.0"}) == ("::1", 8200)
