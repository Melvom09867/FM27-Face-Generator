import pytest


@pytest.fixture(autouse=True)
def no_model_download(monkeypatch, tmp_path):
    """Tests laden nie das große Freistell-Modell herunter und schreiben nichts ins echte Benutzerverzeichnis."""
    from fm27facegen import segment
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setattr(segment, "ensure_model", lambda status=None: False)
    monkeypatch.setattr(segment, "_net", None)
