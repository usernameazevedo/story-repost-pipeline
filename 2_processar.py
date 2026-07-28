#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Etapa 2: apaga os textos do story, aplica um retoque leve e enquadra para o feed.

Le de cada ficha do config:
  arroba  @ de quem publicou o story (vai para a legenda e, com "selo", para a foto)
  rot     graus de rotacao antes de tudo (-90 gira no sentido horario)
  apagar  retangulos [x0, y0, x1, y1] em fracao da imagem recortada, apagados por inpainting
  ancora  posicao do recorte final: y0 em retrato, x0 em paisagem (fracao, 0 = topo/esquerda)

Sempre que der, prefira tirar o texto pelo enquadramento (ancora) em vez de apagar:
o corte nao inventa pixel nenhum. O inpainting fica para texto no meio da foto.

Gera saida/2_limpo (sem texto, resolucao cheia) e saida/3_final (JPEG no formato do feed).
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import comum


def srgb_para_linear(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def linear_para_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def luz(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def branco(lin, forca):
    """Estima a dominante de cor usando os pixels claros e pouco saturados da cena
    (papel, embalagem, parede). Sem branco na cena, cai para media global."""
    flat = lin.reshape(-1, 3)
    l = luz(lin).reshape(-1)
    mx, mn = flat.max(1), flat.min(1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    claros = (l >= np.percentile(l, 85)) & (l <= np.percentile(l, 99.5))
    idx = np.where(claros)[0]
    conf, ref = 0.0, None
    if idx.size > 300:
        cand = idx[sat[idx] <= np.percentile(sat[idx], 30)]
        if cand.size > 100:
            ref = np.median(flat[cand], axis=0)
            conf = float(np.clip((0.45 - float(np.median(sat[cand]))) / 0.35, 0, 1))
    media = flat.mean(axis=0)
    est = conf * (ref / ref[1]) + (1 - conf) * (media / media[1]) if ref is not None \
        else media / media[1]
    ganho = np.array([1.0 / est[0], 1.0, 1.0 / est[2]])
    return np.clip(1 + forca * (0.5 + 0.5 * conf) * (ganho - 1), 0.85, 1.20)


def rgb_para_hsv(a):
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    nz = d > 1e-8
    i = nz & (mx == r); h[i] = ((g - b)[i] / d[i]) % 6
    i = nz & (mx == g); h[i] = ((b - r)[i] / d[i]) + 2
    i = nz & (mx == b); h[i] = ((r - g)[i] / d[i]) + 4
    return h * 60, np.where(mx > 1e-8, d / np.maximum(mx, 1e-8), 0), mx


def hsv_para_rgb(h, s, v):
    h = (h % 360) / 60.0
    i = np.floor(h).astype(int)
    f = h - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    i = i % 6
    out = np.zeros(h.shape + (3,), np.float64)
    for k, canal in enumerate([(v, t, p), (q, v, p), (p, v, t),
                               (p, q, v), (t, p, v), (v, p, q)]):
        m = i == k
        out[m] = np.stack(canal, -1)[m]
    return out


def retoque(img: Image.Image, r: dict) -> Image.Image:
    """Retoque discreto: acerta a luz e a cor sem deixar a foto com cara de filtro."""
    a = np.asarray(img).astype(np.float64) / 255.0
    lin = srgb_para_linear(a)
    lin = np.clip(lin * branco(lin, r["wb"]), 0, 1)

    p95 = float(np.percentile(luz(lin), 95))
    if p95 > 1e-4:
        ev = np.clip(np.log2(r["exposicao"] / p95), -r["exposicao_max"], r["exposicao_max"])
        lin = np.clip(lin * (2.0 ** ev), 0, 1)

    a = linear_para_srgb(lin)

    preto = min(float(np.percentile(luz(a), 0.25)), 0.10)      # ponto de preto real
    a = np.clip((a - preto * 0.85) / (1 - preto * 0.85), 0, 1)

    k = r["contraste"]
    a = np.clip((1 - k) * a + k * (a * a * (3 - 2 * a)), 0, 1)  # curva S suave

    h, s, v = rgb_para_hsv(a)
    s = np.clip(s * (1 + r["vibrance"] * (1 - s) ** 1.5), 0, 1)  # so o que esta apagado
    a = np.clip(hsv_para_rgb(h, s, v), 0, 1)

    im = Image.fromarray((a * 255 + 0.5).astype(np.uint8))
    borrado = np.asarray(im.filter(ImageFilter.GaussianBlur(radius=max(im.size) / 90)))
    a = np.clip(a + r["clareza"] * (a - borrado.astype(np.float64) / 255.0), 0, 1)

    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    raio = np.sqrt(((xx / a.shape[1] - .5) * 2) ** 2 + ((yy / a.shape[0] - .5) * 2) ** 2)
    a = np.clip(a * (1 - r["vinheta"] * np.clip(raio - .55, 0, None) / .85)[..., None], 0, 1)

    im = Image.fromarray((a * 255 + 0.5).astype(np.uint8))
    return im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=r["nitidez"], threshold=3))


FONTES = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",   # macOS
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
    "C:/Windows/Fonts/arialbd.ttf",                        # Windows
)


def fonte(caminho, px: int):
    """Fonte em negrito no tamanho pedido, com queda para a fonte embutida do Pillow."""
    for c in ([caminho] if caminho else []) + list(FONTES):
        try:
            return ImageFont.truetype(c, px)
        except OSError:
            continue
    return ImageFont.load_default()


def selo(img: Image.Image, texto: str, cfg: dict) -> Image.Image:
    """Grava o @ do autor numa pilula escura no canto inferior esquerdo."""
    if not texto:
        return img
    w, h = img.size
    px = max(12, round(cfg["tamanho"] * w))
    margem = round(cfg["margem"] * w)
    folga_x, folga_y = round(px * 0.75), round(px * 0.42)

    f = fonte(cfg.get("fonte"), px)
    camada = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dc = ImageDraw.Draw(camada)
    x0, y0, x1, y1 = dc.textbbox((0, 0), texto, font=f)
    cx, cy = x1 - x0 + 2 * folga_x, y1 - y0 + 2 * folga_y
    caixa = (margem, h - margem - cy, margem + cx, h - margem)
    dc.rounded_rectangle(caixa, radius=cy // 2,
                         fill=(0, 0, 0, round(255 * cfg["opacidade"])))
    dc.text((caixa[0] + folga_x - x0, caixa[1] + folga_y - y0), texto,
            font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(img.convert("RGBA"), camada).convert("RGB")


def enquadra(img: Image.Image, ancora: float, larg: int, alt: int) -> Image.Image:
    """Recorta na proporcao do feed usando a ancora da ficha e entrega no tamanho final."""
    w, h = img.size
    alvo = larg / alt
    if w / h > alvo:                       # paisagem: corta na largura
        cw = int(round(h * alvo))
        x0 = max(0, min(int(round(ancora * w)), w - cw))
        caixa = (x0, 0, x0 + cw, h)
    else:                                  # retrato: corta na altura
        ch = int(round(w / alvo))
        y0 = max(0, min(int(round(ancora * h)), h - ch))
        caixa = (0, y0, w, y0 + ch)
    return img.crop(caixa).resize((larg, alt), Image.LANCZOS)


def main() -> None:
    p = comum.parser(__doc__.splitlines()[0])
    p.add_argument("--somente", nargs="*", metavar="NOME",
                   help="reprocessa apenas estes prints")
    p.add_argument("--reusar-limpo", action="store_true",
                   help="pula o inpainting e parte do que ja esta em saida/2_limpo")
    args = p.parse_args()
    cfg, base = comum.carrega(args.config)

    d_in = os.path.join(base, cfg["saida"], "1_recortado")
    d_limpo = comum.pasta(base, cfg, "2_limpo")
    d_final = comum.pasta(base, cfg, "3_final")
    larg, alt = cfg["formato"]["largura"], cfg["formato"]["altura"]
    lama = None

    for stem, _ in comum.entradas(base, cfg):
        if args.somente and stem not in args.somente:
            continue
        f = comum.ficha(cfg, stem)
        pronto = os.path.join(d_limpo, stem + ".png")
        if args.reusar_limpo and os.path.exists(pronto):
            img = Image.open(pronto).convert("RGB")
            f = {**f, "apagar": [], "rot": 0}
        else:
            img = Image.open(os.path.join(d_in, stem + ".png")).convert("RGB")
        if f["rot"]:
            img = img.rotate(f["rot"], expand=True)

        if f["apagar"]:
            if lama is None:
                from simple_lama_inpainting import SimpleLama
                lama = SimpleLama()
            w, h = img.size
            mascara = np.zeros((h, w), np.uint8)
            for x0, y0, x1, y1 in f["apagar"]:
                mascara[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 255
            img = lama(img, Image.fromarray(mascara)).convert("RGB").crop((0, 0, w, h))
        img.save(os.path.join(d_limpo, stem + ".png"))

        final = enquadra(retoque(img, cfg["retoque"]), f.get("ancora", 0.0), larg, alt)
        if cfg["selo"]["ativo"] and f["arroba"]:
            final = selo(final, "@" + f["arroba"], cfg["selo"])
        final.save(os.path.join(d_final, stem + ".jpg"), quality=93, subsampling=0)
        print(stem, "ok", "@" + f["arroba"] if f["arroba"] else "(sem @)")


if __name__ == "__main__":
    main()
