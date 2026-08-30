"""Testes do acesso ao bucket do Google Cloud Storage.

Cobrem apenas as partes puras (parsing de URI e montagem de URL) e o download
por HTTPS com um servidor local — nada aqui toca a rede externa.
"""

import functools
import http.server
import threading
import urllib.error
import urllib.request

import pytest

from acidentes_trabalho.dados import gcs


@pytest.mark.parametrize(
    ("uri", "esperado"),
    [
        ("gs://ufpr-ppgcd-cat/cat/2023.csv", ("ufpr-ppgcd-cat", "cat/2023.csv")),
        (
            "https://storage.googleapis.com/ufpr-ppgcd-cat/cat/2023.csv",
            ("ufpr-ppgcd-cat", "cat/2023.csv"),
        ),
        (
            "https://ufpr-ppgcd-cat.storage.googleapis.com/cat/2023.csv",
            ("ufpr-ppgcd-cat", "cat/2023.csv"),
        ),
        (
            "https://console.cloud.google.com/storage/browser/_details/ufpr-ppgcd-cat/2023.csv",
            ("ufpr-ppgcd-cat", "2023.csv"),
        ),
    ],
)
def test_parse_uri_reconhece_as_formas_usuais(uri, esperado):
    assert gcs.parse_uri(uri) == esperado


def test_parse_uri_decodifica_nome_com_espaco():
    bucket, objeto = gcs.parse_uri("gs://meu-bucket/Dados%20CAT/2023.csv")
    assert (bucket, objeto) == ("meu-bucket", "Dados CAT/2023.csv")


def test_parse_uri_ignora_query_da_url_assinada():
    uri = "https://storage.googleapis.com/b/o.csv?X-Goog-Signature=abc&X-Goog-Expires=900"
    assert gcs.parse_uri(uri) == ("b", "o.csv")


@pytest.mark.parametrize("uri", ["gs://so-bucket", "arquivo.csv", "ftp://x/y", ""])
def test_parse_uri_rejeita_uri_incompleta(uri):
    with pytest.raises(ValueError):
        gcs.parse_uri(uri)


def test_url_publica_escapa_o_nome_do_objeto():
    assert gcs.url_publica("b", "Dados CAT/2023.csv") == (
        "https://storage.googleapis.com/b/Dados%20CAT/2023.csv"
    )


def test_reconhece_url_assinada():
    assert gcs._e_url_assinada("https://storage.googleapis.com/b/o?X-Goog-Signature=abc")
    assert gcs._e_url_assinada("https://storage.googleapis.com/b/o?Signature=abc")
    assert not gcs._e_url_assinada("https://storage.googleapis.com/b/o")


def test_baixar_sem_bucket_avisa_o_que_falta(monkeypatch):
    monkeypatch.setattr(gcs, "BUCKET_PADRAO", "")
    with pytest.raises(ValueError, match="BUCKET_CAT"):
        gcs.baixar("cat_2023.csv")


class _HandlerSilencioso(http.server.SimpleHTTPRequestHandler):
    """Serve arquivos sem poluir a saida dos testes com log de acesso."""

    def log_message(self, formato, *args):  # noqa: A002 - assinatura da stdlib
        pass


@pytest.fixture
def servidor(tmp_path, monkeypatch):
    """Sobe um servidor HTTP local servindo ``tmp_path``."""
    # Garante que o download nao seja desviado para um proxy corporativo.
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    monkeypatch.setattr(urllib.request, "_opener", None)

    handler = functools.partial(_HandlerSilencioso, directory=str(tmp_path))
    httpd = http.server.HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", tmp_path
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_baixar_url_grava_o_conteudo(servidor, tmp_path):
    base, raiz = servidor
    (raiz / "cat.csv").write_text("uf;total\nPR;10\n", encoding="latin-1")
    destino = tmp_path / "saida" / "cat.csv"

    gravado = gcs.baixar_url(f"{base}/cat.csv", destino)

    assert gravado == destino
    assert destino.read_text(encoding="latin-1") == "uf;total\nPR;10\n"


def test_baixar_url_nao_deixa_arquivo_parcial_em_caso_de_erro(servidor, tmp_path):
    base, _ = servidor
    destino = tmp_path / "saida" / "inexistente.csv"

    with pytest.raises(urllib.error.HTTPError):
        gcs.baixar_url(f"{base}/inexistente.csv", destino)

    assert not destino.exists()
    assert not list(destino.parent.glob("*.parcial"))
