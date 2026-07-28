#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Etapa 1: tira a interface do app dos prints e prepara o material de leitura.

Gera:
  saida/1_recortado/   a foto do story sem barra de status, cabecalho e barra inferior
  saida/_reguas/       a mesma imagem com uma grade em % , para medir textos e enquadramento
  saida/_arrobas.png   os cabecalhos ampliados 3x, empilhados, para conferir o @ de cada autor
  saida/_avatar.png    a foto de perfil recortada do primeiro print (opcional, para a previa)

Tambem imprime o esqueleto do bloco "fotos" do config para os prints ainda nao fichados.
"""
import json

from PIL import Image, ImageDraw

import comum


def grade(img: Image.Image) -> Image.Image:
    """Copia da imagem com linhas a cada 10% na horizontal e 5% na vertical."""
    g = img.copy()
    d = ImageDraw.Draw(g)
    w, h = g.size
    for i in range(1, 10):
        x = w * i // 10
        d.line([(x, 0), (x, h)], fill=(255, 0, 255), width=2)
        d.text((x + 4, 6), str(i * 10), fill=(255, 0, 255))
    for i in range(1, 20):
        y = h * i // 20
        d.line([(0, y), (w, y)], fill=(0, 255, 255), width=2)
        d.text((6, y + 4), str(i * 5), fill=(0, 255, 255))
    return g


def main() -> None:
    args = comum.parser(__doc__.splitlines()[0]).parse_args()
    cfg, base = comum.carrega(args.config)
    d_out = comum.pasta(base, cfg, "1_recortado")
    d_reg = comum.pasta(base, cfg, "_reguas")

    cabecalhos, faltando = [], {}
    for stem, caminho in comum.entradas(base, cfg):
        orig = Image.open(caminho).convert("RGB")
        w, h = orig.size

        orig.crop(comum.caixa(cfg, "recorte_ui", w, h)).save("%s/%s.png" % (d_out, stem))

        g = grade(Image.open("%s/%s.png" % (d_out, stem)))
        g.thumbnail((520, 1200))
        g.save("%s/%s.jpg" % (d_reg, stem), quality=88)

        c = orig.crop(comum.caixa(cfg, "cabecalho", w, h))
        cabecalhos.append((stem, c.resize((c.width * 3, c.height * 3), Image.LANCZOS)))

        if stem not in cfg["fotos"]:
            faltando[stem] = {"arroba": "", "rot": 0, "apagar": [], "ancora": 0.0}

    if cabecalhos:
        cw, ch = cabecalhos[0][1].size
        folha = Image.new("RGB", (cw, (ch + 8) * len(cabecalhos)), (0, 0, 0))
        for i, (_, c) in enumerate(cabecalhos):
            folha.paste(c, (0, i * (ch + 8)))
        folha.save("%s/_arrobas.png" % comum.pasta(base, cfg))
        print("ordem em _arrobas.png:", ", ".join(s for s, _ in cabecalhos))

        primeiro = comum.entradas(base, cfg)[0][1]
        im = Image.open(primeiro).convert("RGB")
        w, h = im.size
        im.crop((int(0.0227 * w), int(0.0809 * h), int(0.1273 * w), int(0.1290 * h))) \
          .resize((160, 160), Image.LANCZOS).save("%s/_avatar.png" % comum.pasta(base, cfg))

    print("%d prints recortados em %s" % (len(cabecalhos), d_out))
    if faltando:
        print("\nfaltam fichas para %d print(s). cole em \"fotos\" no config:\n"
              % len(faltando))
        print(json.dumps(faltando, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
