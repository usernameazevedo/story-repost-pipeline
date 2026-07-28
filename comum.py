# -*- coding: utf-8 -*-
"""Carregamento de configuracao e utilidades compartilhadas pelas 4 etapas."""
from __future__ import annotations

import argparse
import io
import json
import os

EXTENSOES = (".png", ".jpg", ".jpeg", ".heic")

PADRAO = {
    "perfil": "",
    "local": "",
    "hashtags": "",
    "entrada": "prints",
    "saida": "saida",
    "avatar": None,
    # area util do visualizador de stories, em fracao do print inteiro.
    # o padrao vale para prints de iPhone na proporcao 19.5:9.
    "recorte_ui": {"x0": 0.00909, "y0": 0.12204, "x1": 0.99091, "y1": 0.87866},
    # faixa onde aparece o @ de quem publicou o story (etapa 1 amplia para leitura)
    "cabecalho": {"x0": 0.18939, "y0": 0.09589, "x1": 0.80303, "y1": 0.12204},
    "formato": {"largura": 1080, "altura": 1350},
    "retoque": {
        "wb": 0.45,          # forca da correcao de dominante de cor
        "exposicao": 0.72,   # luminancia alvo do percentil 95
        "exposicao_max": 0.30,
        "contraste": 0.10,
        "vibrance": 0.14,
        "clareza": 0.12,
        "nitidez": 40,
        "vinheta": 0.020,
    },
    # selo com o @ do autor gravado na propria imagem (mesmo lugar da previa)
    "selo": {
        "ativo": False,
        "tamanho": 0.030,     # altura da letra, em fracao da largura da imagem
        "margem": 0.026,      # distancia da borda, em fracao da largura
        "opacidade": 0.65,    # fundo da pilula
        "fonte": None,        # caminho de um .ttf/.otf; sem isso usa a fonte do sistema
    },
    "fotos": {},
    "posts": [],
}


def parser(descricao: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=descricao)
    p.add_argument("-c", "--config", default="config.json",
                   help="arquivo de configuracao do cliente (padrao: config.json)")
    return p


def carrega(caminho: str) -> tuple[dict, str]:
    """Devolve (config com defaults aplicados, pasta base do config)."""
    base = os.path.dirname(os.path.abspath(caminho)) or "."
    cfg = json.loads(io.open(caminho, encoding="utf-8").read())
    for chave, valor in PADRAO.items():
        if chave not in cfg:
            cfg[chave] = valor
        elif isinstance(valor, dict):
            cfg[chave] = {**valor, **cfg[chave]}
    return cfg, base


def pasta(base: str, cfg: dict, *partes: str) -> str:
    """Caminho dentro da pasta de saida, ja criado."""
    d = os.path.join(base, cfg["saida"], *partes)
    os.makedirs(d, exist_ok=True)
    return d


def entradas(base: str, cfg: dict) -> list[tuple[str, str]]:
    """Lista [(nome sem extensao, caminho)] dos prints de entrada, em ordem."""
    d = os.path.join(base, cfg["entrada"])
    if not os.path.isdir(d):
        raise SystemExit("pasta de entrada nao encontrada: %s" % d)
    itens = [(os.path.splitext(f)[0], os.path.join(d, f))
             for f in sorted(os.listdir(d)) if f.lower().endswith(EXTENSOES)]
    if not itens:
        raise SystemExit("nenhuma imagem em %s" % d)
    return itens


def ficha(cfg: dict, stem: str) -> dict:
    f = dict(cfg["fotos"].get(stem, {}))
    f.setdefault("arroba", "")
    f.setdefault("rot", 0)
    f.setdefault("apagar", [])
    return f


def caixa(cfg: dict, chave: str, largura: int, altura: int) -> tuple[int, int, int, int]:
    """Converte um retangulo em fracao do config para pixels."""
    c = cfg[chave]
    return (round(c["x0"] * largura), round(c["y0"] * altura),
            round(c["x1"] * largura), round(c["y1"] * altura))
