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

import os
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

from acidentes_trabalho.config import DADOS_RAW

HOST_GCS = "storage.googleapis.com"

# Bucket padrao do projeto; sobrescrito pela variavel de ambiente BUCKET_CAT.
BUCKET_PADRAO = os.getenv("BUCKET_CAT", "")


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


def baixar_url(url: str, destino: Path) -> Path:
    """Baixa ``url`` para ``destino``, em streaming, e devolve o caminho gravado."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    try:
        with urllib.request.urlopen(url) as resposta, parcial.open("wb") as saida:
            shutil.copyfileobj(resposta, saida)
        parcial.replace(destino)
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


def listar(bucket: str | None = None, prefixo: str = "") -> list[str]:
    """Lista os objetos de ``bucket`` sob ``prefixo``. Exige credenciais."""
    from google.cloud import storage  # extra opcional: pip install -e ".[gcs]"

    nome_bucket = bucket or BUCKET_PADRAO
    if not nome_bucket:
        raise ValueError("bucket nao informado: passe bucket=... ou defina BUCKET_CAT")
    cliente = storage.Client()
    return [blob.name for blob in cliente.list_blobs(nome_bucket, prefix=prefixo)]


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
    args = parser.parse_args(argv)

    if args.listar:
        for nome in listar(args.bucket, args.prefixo):
            print(nome)
        return 0

    if not args.uris:
        parser.error("informe ao menos uma URI, ou use --listar")

    for uri in args.uris:
        destino = baixar(uri, bucket=args.bucket)
        print(f"{uri} -> {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
