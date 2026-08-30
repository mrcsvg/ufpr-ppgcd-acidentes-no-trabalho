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
    monkeypatch.delenv(gcs.VARIAVEL_BUCKET, raising=False)
    with pytest.raises(ValueError, match="BUCKET_CAT"):
        gcs.baixar("cat_2023.csv")


def test_bucket_e_lido_do_ambiente_a_cada_chamada(monkeypatch):
    """Em notebook a variavel costuma ser definida depois do import."""
    monkeypatch.delenv(gcs.VARIAVEL_BUCKET, raising=False)
    assert gcs.bucket_padrao() == ""

    monkeypatch.setenv(gcs.VARIAVEL_BUCKET, "meu-bucket")

    assert gcs.bucket_padrao() == "meu-bucket"


def _capturar_bucket(monkeypatch):
    """Substitui a listagem por um espiao que registra o bucket consultado."""
    vistos: list[str] = []

    def falhar(bucket, prefixo):
        raise ImportError("sem google-cloud-storage")

    def espiao(bucket, prefixo):
        vistos.append(bucket)
        return []

    monkeypatch.setattr(gcs, "_listar_autenticado", falhar)
    monkeypatch.setattr(gcs, "_listar_publico", espiao)
    return vistos


def test_bucket_explicito_tem_prioridade_sobre_o_ambiente(monkeypatch):
    monkeypatch.setenv(gcs.VARIAVEL_BUCKET, "do-ambiente")
    vistos = _capturar_bucket(monkeypatch)

    gcs.listar("explicito")

    assert vistos == ["explicito"]


def test_sem_bucket_explicito_usa_o_do_ambiente(monkeypatch):
    monkeypatch.setenv(gcs.VARIAVEL_BUCKET, "do-ambiente")
    vistos = _capturar_bucket(monkeypatch)

    gcs.listar()

    assert vistos == ["do-ambiente"]


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


class _HandlerInstavel(_HandlerSilencioso):
    """Derruba a conexao nas primeiras ``falhas`` requisicoes."""

    falhas = 0

    def do_GET(self):
        if type(self).falhas > 0:
            type(self).falhas -= 1
            # Resposta bem formada, mas com corpo menor que o Content-Length:
            # e assim que uma transferencia cortada chega ao cliente.
            self.send_response(200)
            self.send_header("Content-Length", "999")
            self.end_headers()
            self.wfile.write(b"trunca")
            self.close_connection = True
            return
        super().do_GET()


@pytest.fixture
def servidor_instavel(tmp_path, monkeypatch):
    """Servidor que falha nas duas primeiras requisicoes e depois responde."""
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    monkeypatch.setattr(urllib.request, "_opener", None)
    monkeypatch.setattr(gcs, "ESPERA_INICIAL", 0.01)

    _HandlerInstavel.falhas = 2
    handler = functools.partial(_HandlerInstavel, directory=str(tmp_path))
    httpd = http.server.HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", tmp_path
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_baixar_url_repete_apos_resposta_truncada(servidor_instavel, tmp_path):
    base, raiz = servidor_instavel
    (raiz / "cat.csv").write_text("uf;total\nPR;10\n", encoding="latin-1")
    destino = tmp_path / "saida" / "cat.csv"

    gcs.baixar_url(f"{base}/cat.csv", destino)

    assert destino.read_text(encoding="latin-1") == "uf;total\nPR;10\n"
    assert _HandlerInstavel.falhas == 0, "as duas falhas deveriam ter sido consumidas"


def test_baixar_url_desiste_apos_o_limite_de_tentativas(servidor_instavel, tmp_path):
    base, raiz = servidor_instavel
    _HandlerInstavel.falhas = 99
    (raiz / "cat.csv").write_text("x", encoding="latin-1")
    destino = tmp_path / "saida" / "cat.csv"

    with pytest.raises(gcs.DownloadIncompleto):
        gcs.baixar_url(f"{base}/cat.csv", destino, tentativas=2)

    assert not destino.exists()


def test_baixar_url_nao_repete_em_erro_http(servidor_instavel, tmp_path):
    base, _ = servidor_instavel
    _HandlerInstavel.falhas = 0

    with pytest.raises(urllib.error.HTTPError):
        gcs.baixar_url(f"{base}/nao-existe.csv", tmp_path / "x.csv")
