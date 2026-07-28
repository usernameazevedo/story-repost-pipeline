#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Etapa 4: monta a previa de aprovacao no formato do feed do Instagram.

Uma pagina HTML unica, com carrossel navegavel, o @ do autor marcado em cada slide
e a legenda exatamente como vai ser publicada. Serve para o cliente aprovar.
"""
import html
import io
import os
import shutil

from PIL import Image

import comum

CSS = """
:root{--borda:#dbdbdb;--tinta:#262626;--cinza:#8e8e8e;--azul:#0095f6}
*{margin:0;padding:0;box-sizing:border-box}
body{background:#fafafa;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--tinta)}
.topo{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid var(--borda);padding:12px 16px;text-align:center}
.topo h1{font-size:16px;font-weight:600}
.topo p{font-size:12px;color:var(--cinza);margin-top:2px}
.topo button{position:absolute;right:12px;top:12px;background:var(--azul);color:#fff;border:0;border-radius:99px;padding:7px 14px;font-size:12px;font-weight:600;cursor:pointer}
.feed{max-width:470px;margin:0 auto;padding:24px 0 60px}
.etiqueta{display:inline-block;background:#efefef;color:var(--cinza);font-size:11px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;padding:4px 10px;border-radius:12px;margin:24px 0 8px 4px}
.post{background:#fff;border:1px solid var(--borda);border-radius:8px;overflow:hidden}
.cabecalho{display:flex;align-items:center;padding:10px 12px}
.avatar{width:36px;height:36px;border-radius:50%;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);display:flex;align-items:center;justify-content:center;margin-right:10px;flex-shrink:0;color:#fff;font-weight:700}
.avatar img{width:32px;height:32px;border-radius:50%;border:2px solid #fff;object-fit:cover;background:#fff}
.perfil{font-size:14px;font-weight:600}
.local{font-size:11px;color:var(--cinza)}
.tres{margin-left:auto;font-weight:700;letter-spacing:1px}
.carrossel{position:relative;overflow:hidden;background:#000}
.trilho{display:flex;transition:transform .3s ease}
.trilho img{width:100%;flex-shrink:0;display:block}
.seta{position:absolute;top:50%;transform:translateY(-50%);width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,.9);border:none;cursor:pointer;font-size:15px;line-height:1;color:#262626;box-shadow:0 1px 3px rgba(0,0,0,.3)}
.seta.ant{left:10px}.seta.prox{right:10px}
.contador{position:absolute;top:12px;right:12px;background:rgba(0,0,0,.65);color:#fff;font-size:12px;padding:4px 9px;border-radius:12px}
.marca{position:absolute;left:12px;bottom:12px;background:rgba(0,0,0,.65);color:#fff;font-size:12px;padding:4px 9px;border-radius:12px}
.bolinhas{display:flex;justify-content:center;gap:4px;padding:10px 0 0}
.bolinhas i{width:6px;height:6px;border-radius:50%;background:#c7c7c7}
.bolinhas i.on{background:var(--azul)}
.acoes{display:flex;align-items:center;padding:8px 12px 4px;gap:14px}
.acoes svg{width:24px;height:24px;stroke:var(--tinta);fill:none;stroke-width:2;cursor:pointer}
.acoes .salvar{margin-left:auto}
.creditos{padding:0 12px;font-size:13px;color:var(--cinza)}
.creditos b{color:var(--tinta);font-weight:600}
.legenda{padding:4px 12px 6px;font-size:14px;line-height:1.45;white-space:pre-line}
.legenda b{font-weight:600;margin-right:6px}
.legenda .tags{color:#00376b}
.hora{padding:0 12px 12px;font-size:10px;color:var(--cinza);text-transform:uppercase;letter-spacing:.3px}
"""

JS = """
var cs={};
function monta(id,n){cs[id]={i:0,n:n};pinta(id)}
function vai(id,d){var c=cs[id];c.i=Math.max(0,Math.min(c.n-1,c.i+d));pinta(id)}
function pinta(id){var c=cs[id],t=document.getElementById('t-'+id);
 t.style.transform='translateX('+(-c.i*100)+'%)';
 document.getElementById('c-'+id).textContent=(c.i+1)+'/'+c.n;
 var b=document.getElementById('b-'+id).children;
 for(var k=0;k<b.length;k++)b[k].className=(k===c.i?'on':'');
 var a=t.children[c.i].dataset.autor;
 document.getElementById('m-'+id).textContent=a?'@'+a:'';
 document.getElementById('a-'+id).style.display=c.i===0?'none':'block';
 document.getElementById('p-'+id).style.display=c.i===c.n-1?'none':'block'}
function tela(){document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen()}
addEventListener('keydown',function(e){if(e.key.toLowerCase()==='f'&&!e.metaKey&&!e.ctrlKey)tela()});
"""

ICONES = (
    '<svg viewBox="0 0 24 24"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 1 0-7.8'
    ' 7.8l1 1L12 21.2l7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8z"/></svg>'
    '<svg viewBox="0 0 24 24"><path d="M21 11.5a8.4 8.4 0 0 1-8.5 8.3 8.6 8.6 0 0 1-3.9-.9L3 20l1.2'
    '-5.3a8.2 8.2 0 0 1-.7-3.2A8.4 8.4 0 0 1 12 3.2a8.4 8.4 0 0 1 9 8.3z"/></svg>'
    '<svg viewBox="0 0 24 24"><path d="M22 3 9.2 12.7M22 3l-7.5 18-3.3-8.3L3 9.5 22 3z"/></svg>'
    '<svg class="salvar" viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V3h14v18z"/></svg>'
)


def legenda_html(texto: str, perfil: str, hashtags: str) -> str:
    corpo = texto
    tags = ""
    if hashtags and texto.endswith(hashtags):
        corpo = texto[: -len(hashtags)].rstrip()
        tags = '\n\n<span class="tags">%s</span>' % html.escape(hashtags)
    return "<b>%s</b>%s%s" % (html.escape(perfil), html.escape(corpo), tags)


def main() -> None:
    args = comum.parser(__doc__.splitlines()[0]).parse_args()
    cfg, base = comum.carrega(args.config)
    d_pub = os.path.join(base, cfg["saida"], "4_publicacoes")
    d_out = comum.pasta(base, cfg, "preview")
    d_ass = comum.pasta(base, cfg, "preview", "assets")
    perfil = cfg["perfil"]

    avatar = ""
    if cfg["avatar"]:
        origem = os.path.join(base, cfg["avatar"])
        if os.path.exists(origem):
            shutil.copy(origem, os.path.join(d_ass, "avatar.png"))
            avatar = '<img src="assets/avatar.png" alt="">'
    if not avatar:
        avatar = html.escape(perfil[:1].upper())

    gravado = cfg["selo"]["ativo"]   # com o selo na foto, a previa nao repete a etiqueta
    blocos, inicia = [], []
    for i, post in enumerate(cfg["posts"], 1):
        d = os.path.join(d_pub, post["slug"])
        arquivos = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
        slides, autores = [], []
        for f in arquivos:
            autor = f[2:-4]
            autores.append(autor)
            destino = "%s_%s" % (post["slug"], f)
            Image.open(os.path.join(d, f)).save(os.path.join(d_ass, destino),
                                                quality=84, optimize=True)
            slides.append('<img src="assets/%s" data-autor="%s" alt="">'
                          % (destino, "" if gravado else html.escape(autor)))
        texto = io.open(os.path.join(d, "legenda.txt"), encoding="utf-8").read().strip()
        blocos.append("""
  <div class="etiqueta">Publicação %d %s</div>
  <div class="post">
    <div class="cabecalho">
      <div class="avatar">%s</div>
      <div><div class="perfil">%s</div><div class="local">%s</div></div>
      <div class="tres">...</div>
    </div>
    <div class="carrossel">
      <div class="trilho" id="t-%d">%s</div>
      <button class="seta ant" id="a-%d" onclick="vai(%d,-1)">&#10094;</button>
      <button class="seta prox" id="p-%d" onclick="vai(%d,1)">&#10095;</button>
      <div class="contador" id="c-%d"></div>
      <div class="marca" id="m-%d"></div>
    </div>
    <div class="bolinhas" id="b-%d">%s</div>
    <div class="acoes">%s</div>
    <div class="creditos">Fotos de <b>%s</b></div>
    <div class="legenda">%s</div>
    <div class="hora">%s</div>
  </div>""" % (
            i, "· carrossel (%d páginas)" % len(slides) if len(slides) > 1 else "· foto única",
            avatar, html.escape(perfil), html.escape(cfg["local"]),
            i, "".join(slides), i, i, i, i, i, i, i, "<i></i>" * len(slides), ICONES,
            html.escape(" · ".join("@" + a for a in autores)),
            legenda_html(texto, perfil, cfg["hashtags"]),
            html.escape(post.get("tema", "")) + " · sugestão de publicação"))
        inicia.append("monta(%d,%d)" % (i, len(slides)))

    doc = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · aprovação</title>
<style>%s</style>
</head>
<body>
<div class="topo">
  <h1>@%s</h1>
  <p>%s</p>
  <button onclick="tela()">Tela cheia (F)</button>
</div>
<div class="feed">%s
</div>
<script>%s
%s;
</script>
</body>
</html>
""" % (html.escape(cfg.get("cliente", perfil)), CSS, html.escape(perfil),
       html.escape(cfg.get("subtitulo", "%d publicações para aprovação" % len(cfg["posts"]))),
       "".join(blocos), JS, ";".join(inicia))
    io.open(os.path.join(d_out, "index.html"), "w", encoding="utf-8").write(doc)
    print(os.path.join(d_out, "index.html"))


if __name__ == "__main__":
    main()
