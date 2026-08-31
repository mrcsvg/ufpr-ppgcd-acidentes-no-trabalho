"""Verifica que o notebook do Colab esta integro.

Nao executa o notebook — isso levaria minutos e exigiria os dados. Confere o que
quebra silenciosamente ao versionar: JSON invalido, celula de codigo que nao
compila, saidas esquecidas no arquivo e o link do Colab apontando para o lugar
errado.
"""

import json

import pytest

from acidentes_trabalho.config import RAIZ

NOTEBOOK = RAIZ / "notebooks" / "01_consolidacao_e_eda.ipynb"


@pytest.fixture(scope="module")
def notebook():
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def test_notebook_existe_e_e_json_valido(notebook):
    assert notebook["nbformat"] == 4
    assert notebook["cells"], "notebook sem células"


def test_toda_celula_de_codigo_compila(notebook):
    for i, celula in enumerate(notebook["cells"]):
        if celula["cell_type"] != "code":
            continue
        fonte = "".join(celula["source"])
        # Linhas mágicas do Jupyter (!pip, %cd, %%time) não são Python válido.
        limpo = "\n".join(
            "pass" if linha.lstrip().startswith(("!", "%")) else linha
            for linha in fonte.splitlines()
        )
        try:
            compile(limpo, f"celula_{i}", "exec")
        except SyntaxError as erro:
            pytest.fail(f"célula {i} não compila: {erro}")


def test_notebook_vai_versionado_sem_saidas(notebook):
    """Saídas commitadas incham o diff e vazam dados nos revisores."""
    com_saida = [
        i for i, c in enumerate(notebook["cells"])
        if c["cell_type"] == "code" and c.get("outputs")
    ]
    assert not com_saida, f"células com saída gravada: {com_saida}"


def test_link_do_colab_aponta_para_este_arquivo(notebook):
    cabecalho = "".join(notebook["cells"][0]["source"])

    assert "colab.research.google.com/github/" in cabecalho
    assert NOTEBOOK.name in cabecalho


def test_notebook_instala_o_pacote_antes_de_importar(notebook):
    """No Colab o pacote não existe: a primeira célula de código tem que instalá-lo."""
    codigo = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    primeira = "".join(codigo[0]["source"])

    assert "clone" in primeira, "a célula precisa trazer o repositório"
    assert '"pip", "install"' in primeira, "e instalar o pacote"
    # sys.executable -m pip, e nao "!pip": no Colab o shell pode apontar para
    # outro interpretador, instalar nele, e o import falhar em seguida com
    # ModuleNotFoundError.
    assert "sys.executable" in primeira
    # Rede de seguranca para o caso de o editable nao ser visto pelo kernel.
    assert 'RAIZ / "src"' in primeira
    assert "invalidate_caches" in primeira


def test_setup_verifica_que_o_import_funcionou(notebook):
    """A celula precisa falhar alto, nao seguir e quebrar tres celulas depois."""
    primeira = "".join(
        [c for c in notebook["cells"] if c["cell_type"] == "code"][0]["source"]
    )

    assert "check=True" in primeira, "erro de instalação tem que interromper"
    assert "import acidentes_trabalho" in primeira, "confirma o import na própria célula"
