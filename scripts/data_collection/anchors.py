"""Generation of the anchor texts with the OpenAI Responses API.

Ported from the notebook of the run of 12-06-2026 (textos_dimensoes, version with
three lengths), which produced data/ancoras_llm_3_versoes.csv and the three files
data/ancoras_v*_palavras.csv. The prompt, the model, the word intervals, the token
limit and the order of the 18 calls are those of that run. The prompt stays in
Portuguese because it is part of the procedure that generated the data.

Differences from the original notebook:
- the key is read with scripts.api_keys.get_api_key, never written in the code;
- the call is made with `requests` (already in environment.yaml) and not with the
  OpenAI SDK, so that the reference environment and its lockfile stay unchanged.
  The request has the same fields as client.responses.create(model=..., input=...,
  max_output_tokens=...), and output_text() reproduces response.output_text.

temperature, top_p and the seed were not fixed in the original run, so a new run
produces different texts: the analysis uses the preserved CSV files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

from ..api_keys import get_api_key
from .snapshot import ensure_outside_data_dir

API_URL = "https://api.openai.com/v1/responses"
MODEL = "gpt-5.4-mini"

ANCHOR_VERSIONS = {
    "v1_50_palavras": {"palavras_alvo": 50, "min_palavras": 45, "max_palavras": 60},
    "v2_100_palavras": {"palavras_alvo": 100, "min_palavras": 95, "max_palavras": 115},
    "v3_150_palavras": {"palavras_alvo": 150, "min_palavras": 140, "max_palavras": 170},
}

DIMENSION_NAMES = {
    "Governança inteligente": "Governança Inteligente",
    "Sociedade inteligente": "Sociedade Inteligente",
    "Mobilidade Inteligente": "Mobilidade Inteligente",
    "Ambiente Inteligente": "Ambiente Inteligente",
    "Qualidade de vida inteligente": "Qualidade de Vida Inteligente",
    "Economia inteligente": "Economia Inteligente",
}

PROMPT_TEMPLATE = """
Tarefa:
Gerar um texto-âncora para embeddings semânticos.

Fonte:
Usa apenas o texto-base fornecido. Não acrescentes conhecimento externo.

Dimensão:
{dimensao}

Texto-base da dimensão:
\"\"\"
{texto_base}
\"\"\"

Regras:
- Usa apenas a informação presente no texto-base.
- Não acrescentes conhecimento externo.
- Escreve em português europeu.
- Produz um único parágrafo.
- O texto deve ser adequado para embeddings semânticos.
- O texto deve representar claramente a dimensão "{dimensao}".
- O texto deve ter aproximadamente {palavras_alvo} palavras.
- O texto deve ter entre {min_palavras} e {max_palavras} palavras.
- Evita listas, enumerações e bullets.
- Evita frases vagas como "esta dimensão é importante".
- Mantém linguagem clara e descritiva.
- Não devolvas explicações adicionais.

Devolve apenas JSON válido com esta estrutura:
{{
  "dimensao": "{dimensao}",
  "texto_ancora": "..."
}}
"""


def read_base_text(path: Path) -> pd.DataFrame:
    """Reads texto_base.csv exactly as in the original run.

    latin-1 is kept so that the prompts are identical to those sent on 12-06-2026.
    With this encoding, the «€» and «‰» of the base text (bytes 0x80 and 0x89 in
    Windows-1252) reach the model as control characters; the analysis notebooks
    read the same file in cp1252.
    """
    df_base = pd.read_csv(path, sep=None, engine="python", encoding="latin1")
    df_base.columns = df_base.columns.str.strip().str.lower()
    df_base["dimensao"] = df_base["dimensao"].astype(str).str.strip().replace(DIMENSION_NAMES)
    df_base["texto"] = df_base["texto"].astype(str).str.replace("\r\n", " ", regex=False).str.strip()
    return df_base


def build_prompt(dimensao, texto_base, palavras_alvo, min_palavras, max_palavras) -> str:
    return PROMPT_TEMPLATE.format(
        dimensao=dimensao, texto_base=texto_base, palavras_alvo=palavras_alvo,
        min_palavras=min_palavras, max_palavras=max_palavras,
    )


def output_text(response: dict) -> str:
    """Text of the answer, equivalent to the response.output_text property of the SDK."""
    return "".join(
        part.get("text", "")
        for item in response.get("output", []) if item.get("type") == "message"
        for part in item.get("content", []) if part.get("type") == "output_text"
    )


def generate_anchor(session, dimensao, texto_base, version, model=MODEL) -> dict:
    """One call to the Responses API; returns {"dimensao": ..., "texto_ancora": ...}."""
    config = ANCHOR_VERSIONS[version]
    r = session.post(API_URL, json={
        "model": model,
        "input": build_prompt(dimensao, texto_base, **config),
        "max_output_tokens": int(config["palavras_alvo"] * 4) + 200,
    }, timeout=120)
    r.raise_for_status()
    texto_resposta = output_text(r.json())

    try:
        return json.loads(texto_resposta)
    except json.JSONDecodeError:
        print("The response is not valid JSON. Response received:")
        print(texto_resposta)
        raise


def generate_all_versions(session, df_base, model=MODEL) -> pd.DataFrame:
    """18 calls, one per version and per dimension, in the order of the original run."""
    rows = []
    for version in ANCHOR_VERSIONS:
        print(f"Version: {version}")
        for _, row in df_base.iterrows():
            print(f"  - {row['dimensao']}")
            result = generate_anchor(session, row["dimensao"], row["texto"], version, model)
            result["versao"] = version
            rows.append(result)

    df = pd.DataFrame(rows)
    df["num_palavras"] = df["texto_ancora"].apply(lambda x: len(str(x).split()))
    df["palavras_alvo"] = df["versao"].map({k: v["palavras_alvo"] for k, v in ANCHOR_VERSIONS.items()})
    return df


def word_count_check(df_anchors: pd.DataFrame) -> pd.DataFrame:
    """Word count of each anchor against the interval requested in the prompt."""
    limits = pd.DataFrame.from_dict(ANCHOR_VERSIONS, orient="index").rename_axis("versao").reset_index()
    check = df_anchors[["versao", "dimensao", "num_palavras"]].merge(limits, on="versao")
    check["in_interval"] = check["num_palavras"].between(check["min_palavras"], check["max_palavras"])
    return check


def export_anchors(base_file: Path, output_file: Path, model=MODEL) -> pd.DataFrame:
    """Generates the 18 anchors and writes them to output_file (CSV with ';', UTF-8 with BOM).

    Requires OPENAI_API_KEY (see .env.example) and has a cost on the user's account.
    """
    output_file = ensure_outside_data_dir(output_file)
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {get_api_key('OPENAI_API_KEY')}"

    df = generate_all_versions(session, read_base_text(base_file), model)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, sep=";", index=False, encoding="utf-8-sig")
    return df
