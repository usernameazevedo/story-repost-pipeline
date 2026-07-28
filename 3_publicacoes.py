#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Etapa 3: agrupa as fotos tratadas em publicacoes e escreve as legendas.

Cada item de "posts" no config vira uma pasta com as fotos na ordem das paginas
(o @ do autor entra no nome do arquivo) mais um legenda.txt pronto para colar.
"""
import io
import os
import shutil

import comum


def main() -> None:
    args = comum.parser(__doc__.splitlines()[0]).parse_args()
    cfg, base = comum.carrega(args.config)
    d_final = os.path.join(base, cfg["saida"], "3_final")
    d_out = os.path.join(base, cfg["saida"], "4_publicacoes")
    if os.path.isdir(d_out):
        shutil.rmtree(d_out)

    if not cfg["posts"]:
        raise SystemExit('nada em "posts" no config')

    linhas = ["# Publicacoes - %s" % cfg.get("cliente", cfg["perfil"]), ""]
    for i, post in enumerate(cfg["posts"], 1):
        d = os.path.join(d_out, post["slug"])
        os.makedirs(d)
        autores = []
        for j, stem in enumerate(post["fotos"], 1):
            arroba = comum.ficha(cfg, stem)["arroba"] or stem
            autores.append(arroba)
            origem = os.path.join(d_final, stem + ".jpg")
            if not os.path.exists(origem):
                raise SystemExit("falta %s (rode a etapa 2)" % origem)
            shutil.copy(origem, os.path.join(d, "%d_%s.jpg" % (j, arroba)))

        texto = post["legenda"].rstrip()
        if cfg["hashtags"]:
            texto += "\n\n" + cfg["hashtags"]
        io.open(os.path.join(d, "legenda.txt"), "w", encoding="utf-8").write(texto + "\n")

        linhas += ["## Post %d - %s (`%s`)" % (i, post.get("tema", ""), post["slug"]), "",
                   " | ".join("Pagina %d: @%s" % (k, a) for k, a in enumerate(autores, 1)),
                   "", "```", texto, "```", ""]
        print(post["slug"], "->", ", ".join("@" + a for a in autores))

    io.open(os.path.join(d_out, "LEGENDAS.md"), "w", encoding="utf-8") \
        .write("\n".join(linhas))
    print("\n%d publicacoes em %s" % (len(cfg["posts"]), d_out))


if __name__ == "__main__":
    main()
