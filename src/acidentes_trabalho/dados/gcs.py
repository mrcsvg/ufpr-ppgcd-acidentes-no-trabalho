"""Download dos dados a partir de um bucket do Google Cloud Storage.

Dois caminhos de acesso, escolhidos automaticamente:

- **sem credencial**: objeto publico ou URL assinada, baixado por HTTPS direto;
- **com credencial**: usa ``google-cloud-storage`` (extra ``gcs`` do projeto) com
  as credenciais padrao do ambiente (``gcloud auth application-default login`` ou
  ``GOOGLE_APPLICATION_CREDENTIALS``).

O bucket do projeto e configurado por ``BUCKET_CAT`` (variavel de ambiente) ou
passado explicitamente em cada chamada.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from acidentes_trabalho.config import DADOS_RAW

HOST_GCS = "storage.googleapis.com"

# Transferencias longas caem; repetir com espera crescente resolve na pratica.
TENTATIVAS = 5
ESPERA_INICIAL = 2.0


class DownloadIncompleto(OSError):
    """O corpo recebido e menor que o ``Content-Length`` anunciado."""

# Bucket padrao do projeto; sobrescrito pela variavel de ambiente BUCKET_CAT.
BUCKET_PADRAO = os.getenv("BUCKET_CAT", "")


@dataclass(frozen=True)
class Objeto:
    """Um objeto do bucket: nome completo e tamanho em bytes."""

    nome: str
    tamanho: int


def parse_uri(uri: str) -> tuple[str, str]:
    """Separa ``uri`` em ``(bucket, objeto)``.

    Aceita as formas usuais de referenciar um objeto do GCS::

        gs://meu-bucket/pasta/arquivo.csv
        https://storage.googleapis.com/meu-bucket/pasta/arquivo.csv
        https://meu-bucket.storage.googleapis.com/pasta/arquivo.csv
        https://console.cloud.google.com/storage/browser/_details/meu-bucket/arquivo.csv

    Uma URL assinada mantem a query string fora do nome do objeto.

    Raises:
        ValueError: se ``uri`` nao identificar bucket e objeto.
    """
    uri = uri.strip()

    if uri.startswith("gs://"):
        resto = uri[len("gs://") :]
        bucket, _, objeto = resto.partition("/")
    else:
        partes = urllib.parse.urlsplit(uri)
        if partes.scheme not in ("http", "https"):
            raise ValueError(f"URI nao reconhecida: {uri!r}")
        caminho = partes.path.lstrip("/")
        if partes.netloc.endswith(f".{HOST_GCS}"):
            bucket = partes.netloc[: -len(f".{HOST_GCS}")]
            objeto = caminho
        else:
            if caminho.startswith("storage/browser/_details/"):
                caminho = caminho[len("storage/browser/_details/") :]
            bucket, _, objeto = caminho.partition("/")

    objeto = urllib.parse.unquote(objeto)
    if not bucket or not objeto:
        raise ValueError(f"nao foi possivel extrair bucket e objeto de {uri!r}")
    return bucket, objeto


def url_publica(bucket: str, objeto: str) -> str:
    """Monta a URL HTTPS de leitura de ``objeto`` em ``bucket``."""
    return f"https://{HOST_GCS}/{bucket}/{urllib.parse.quote(objeto)}"


def _e_url_assinada(uri: str) -> bool:
    """Indica se ``uri`` ja carrega assinatura na query string."""
    query = urllib.parse.urlsplit(uri).query
    return "Signature=" in query or "X-Goog-Signature=" in query


def baixar_url(url: str, destino: Path, *, tentativas: int = TENTATIVAS) -> Path:
    """Baixa ``url`` para ``destino``, em streaming, e devolve o caminho gravado.

    Transferencias longas sao cortadas de vez em quando ("connection reset by
    peer"), sobretudo atraves de proxy. Cada tentativa recomeca o arquivo, com
    espera crescente entre elas; a gravacao vai para um ``.parcial`` que so vira
    o arquivo final quando o download termina, entao uma falha nunca deixa
    arquivo truncado no lugar do bom.

    Nem toda queda vira excecao: uma resposta cortada no meio simplesmente
    termina antes da hora, e a copia em streaming a aceita em silencio. Por isso
    o total gravado e conferido contra o ``Content-Length`` anunciado, e a
    divergencia conta como falha - senao o arquivo truncado passaria por bom.

    Raises:
        DownloadIncompleto: se o corpo recebido for menor que o anunciado em
            todas as tentativas.
        HTTPError: imediatamente, sem repetir, quando o servidor recusa (4xx).
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    try:
        for tentativa in range(1, tentativas + 1):
            try:
                with urllib.request.urlopen(url) as resposta, parcial.open("wb") as saida:
                    shutil.copyfileobj(resposta, saida)
                    anunciado = resposta.headers.get("Content-Length")
                gravado = parcial.stat().st_size
                if anunciado is not None and gravado != int(anunciado):
                    raise DownloadIncompleto(
                        f"{destino.name}: recebidos {gravado} bytes de {anunciado}"
                    )
                parcial.replace(destino)
                return destino
            except urllib.error.HTTPError:
                raise  # 404, 403: repetir nao ajuda
            except (
                DownloadIncompleto,
                urllib.error.URLError,
                TimeoutError,
                ConnectionError,
                OSError,
            ):
                if tentativa == tentativas:
                    raise
                time.sleep(ESPERA_INICIAL * 2 ** (tentativa - 1))
    finally:
        parcial.unlink(missing_ok=True)
    return destino


def baixar(
    uri: str,
    destino: Path | None = None,
    *,
    bucket: str | None = None,
    autenticado: bool | None = None,
) -> Path:
    """Baixa um objeto do GCS para ``data/raw/`` (ou para ``destino``).

    Args:
        uri: ``gs://...``, URL HTTPS do objeto, URL assinada, ou apenas o nome do
            objeto quando ``bucket`` (ou ``BUCKET_CAT``) estiver definido.
        destino: caminho de gravacao; por padrao ``data/raw/<nome do objeto>``.
        bucket: bucket a usar quando ``uri`` for so o nome do objeto.
        autenticado: forca o uso de ``google-cloud-storage`` (``True``) ou do
            download HTTPS direto (``False``). Por padrao, detecta pela URI:
            URL assinada baixa direto, o resto tenta autenticado e cai para direto.

    Returns:
        O caminho do arquivo gravado.
    """
    if _e_url_assinada(uri):
        alvo = destino or DADOS_RAW / Path(urllib.parse.urlsplit(uri).path).name
        return baixar_url(uri, alvo)

    if "://" in uri:
        nome_bucket, objeto = parse_uri(uri)
    else:
        nome_bucket = bucket or BUCKET_PADRAO
        objeto = uri.lstrip("/")
        if not nome_bucket:
            raise ValueError(
                "bucket nao informado: passe bucket=... ou defina a variavel BUCKET_CAT"
            )

    alvo = destino or DADOS_RAW / Path(objeto).name

    if autenticado is not False:
        try:
            return _baixar_autenticado(nome_bucket, objeto, alvo)
        except ImportError:
            if autenticado is True:
                raise

    return baixar_url(url_publica(nome_bucket, objeto), alvo)


def _baixar_autenticado(bucket: str, objeto: str, destino: Path) -> Path:
    """Baixa via ``google-cloud-storage`` usando as credenciais do ambiente."""
    from google.cloud import storage  # extra opcional: pip install -e ".[gcs]"

    destino.parent.mkdir(parents=True, exist_ok=True)
    cliente = storage.Client()
    cliente.bucket(bucket).blob(objeto).download_to_filename(destino)
    return destino


def listar(bucket: str | None = None, prefixo: str = "") -> list[Objeto]:
    """Lista os objetos de ``bucket`` sob ``prefixo``.

    Tenta a API autenticada e cai para a API publica de listagem quando nao ha
    credencial — que funciona enquanto o bucket estiver aberto para leitura.
    """
    nome_bucket = bucket or BUCKET_PADRAO
    if not nome_bucket:
        raise ValueError("bucket nao informado: passe bucket=... ou defina BUCKET_CAT")
    try:
        return _listar_autenticado(nome_bucket, prefixo)
    except ImportError:
        return _listar_publico(nome_bucket, prefixo)


def _listar_autenticado(bucket: str, prefixo: str) -> list[Objeto]:
    from google.cloud import storage  # extra opcional: pip install -e ".[gcs]"

    cliente = storage.Client()
    return [
        Objeto(blob.name, blob.size or 0)
        for blob in cliente.list_blobs(bucket, prefix=prefixo)
        if not blob.name.endswith("/")
    ]


def _listar_publico(bucket: str, prefixo: str) -> list[Objeto]:
    """Lista pela API JSON publica, paginando ate o fim."""
    objetos: list[Objeto] = []
    token = None
    while True:
        parametros = {"maxResults": "1000", "fields": "items(name,size),nextPageToken"}
        if prefixo:
            parametros["prefix"] = prefixo
        if token:
            parametros["pageToken"] = token
        url = (
            f"https://www.googleapis.com/storage/v1/b/{urllib.parse.quote(bucket)}/o"
            f"?{urllib.parse.urlencode(parametros)}"
        )
        with urllib.request.urlopen(url) as resposta:
            pagina = json.load(resposta)
        objetos += [
            Objeto(item["name"], int(item.get("size", 0)))
            for item in pagina.get("items", [])
            if not item["name"].endswith("/")
        ]
        token = pagina.get("nextPageToken")
        if not token:
            return objetos


def sincronizar(
    bucket: str | None = None,
    prefixo: str = "",
    destino: Path | None = None,
    *,
    refazer: bool = False,
) -> list[Path]:
    """Baixa para ``destino`` todos os objetos do bucket que ainda faltam.

    Um objeto e considerado ja baixado quando existe um arquivo local de mesmo
    nome e mesmo tamanho; ``refazer=True`` ignora essa verificacao.

    Returns:
        Os caminhos de todos os objetos, baixados agora ou ja presentes.
    """
    pasta = destino or DADOS_RAW
    pasta.mkdir(parents=True, exist_ok=True)
    nome_bucket = bucket or BUCKET_PADRAO

    caminhos = []
    for objeto in listar(nome_bucket, prefixo):
        alvo = pasta / Path(objeto.nome).name
        atual = alvo.stat().st_size if alvo.exists() else -1
        if refazer or atual != objeto.tamanho:
            baixar(objeto.nome, alvo, bucket=nome_bucket)
        caminhos.append(alvo)
    return caminhos


def _main(argv: list[str] | None = None) -> int:
    """CLI: ``python -m acidentes_trabalho.dados.gcs <uri> [<uri> ...]``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m acidentes_trabalho.dados.gcs",
        description="Baixa objetos do bucket do projeto para data/raw/.",
    )
    parser.add_argument("uris", nargs="*", help="gs://..., URL do objeto, ou nome do objeto")
    parser.add_argument("--bucket", default=None, help="bucket (padrao: variavel BUCKET_CAT)")
    parser.add_argument("--prefixo", default="", help="lista os objetos sob este prefixo")
    parser.add_argument("--listar", action="store_true", help="apenas lista, nao baixa")
    parser.add_argument(
        "--sincronizar", action="store_true", help="baixa tudo que falta sob --prefixo"
    )
    args = parser.parse_args(argv)

    if args.listar:
        objetos = listar(args.bucket, args.prefixo)
        for objeto in objetos:
            print(f"{objeto.tamanho/1e6:9.1f} MB  {objeto.nome}")
        print(f"{len(objetos)} objetos, {sum(o.tamanho for o in objetos)/1e9:.2f} GB")
        return 0

    if args.sincronizar:
        caminhos = sincronizar(args.bucket, args.prefixo)
        print(f"{len(caminhos)} arquivos em {caminhos[0].parent}" if caminhos else "nada a baixar")
        return 0

    if not args.uris:
        parser.error("informe ao menos uma URI, ou use --listar / --sincronizar")

    for uri in args.uris:
        destino = baixar(uri, bucket=args.bucket)
        print(f"{uri} -> {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
