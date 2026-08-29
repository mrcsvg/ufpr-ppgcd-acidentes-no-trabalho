"""Testes dos caminhos do projeto."""

from acidentes_trabalho import config


def test_raiz_contem_pyproject():
    assert (config.RAIZ / "pyproject.toml").is_file()


def test_diretorios_de_dados_existem():
    for diretorio in config.DIRETORIOS:
        assert diretorio.is_dir(), f"diretorio ausente: {diretorio}"


def test_garantir_diretorios_e_idempotente(tmp_path, monkeypatch):
    novo = tmp_path / "processed"
    monkeypatch.setattr(config, "DIRETORIOS", (novo,))
    config.garantir_diretorios()
    config.garantir_diretorios()
    assert novo.is_dir()
