# story-repost-pipeline

Pipeline para transformar **prints de stories em que clientes marcaram a marca** em publicações de feed prontas: sem a interface do Instagram, sem o texto que a pessoa escreveu por cima da foto, com um retoque leve de cor e luz, no formato do feed, agrupadas em carrosséis e com a legenda já creditando cada autor.

Nasceu de um caso real: 14 prints de stories de uma hamburgueria viraram 7 carrosséis de 2 páginas em uma tarde, com uma prévia em formato de feed para o cliente aprovar.

## Como funciona

```
prints/*.png
   ├─ 1_recortar.py    → saida/1_recortado/   foto do story sem a UI do app
   │                     saida/_reguas/       a mesma foto com grade em % (para medir)
   │                     saida/_arrobas.png   os cabeçalhos ampliados 3x (para ler os @)
   ├─ 2_processar.py   → saida/2_limpo/       sem o texto do story (inpainting LaMa)
   │                     saida/3_final/       retocada e enquadrada no formato do feed
   ├─ 3_publicacoes.py → saida/4_publicacoes/<slug>/{1_@autor.jpg, 2_@autor.jpg, legenda.txt}
   └─ 4_preview.py     → saida/preview/index.html   prévia em formato de feed, para aprovação
```

Tudo é dirigido por um `config.json` por cliente (veja `config.exemplo.json`). Trocar de cliente é trocar esse arquivo e a pasta de prints.

### 1. Recortar — `1_recortar.py`

Corta a barra de status, o cabeçalho do story e a barra inferior, deixando só a foto. A área é definida em **fração do print** (`recorte_ui`), então o mesmo config serve para qualquer aparelho de mesma proporção; para outro formato de tela, ajuste as quatro frações uma vez.

Como as decisões seguintes dependem de **olhar** as imagens, esta etapa também produz:

- `_reguas/`: cada foto com uma grade em porcentagem, para você anotar onde está o texto e onde cortar;
- `_arrobas.png`: os cabeçalhos dos prints ampliados 3x e empilhados, para conferir o @ de quem publicou letra por letra;
- `_avatar.png`: a foto de perfil recortada, usada na prévia.

No fim ela imprime o esqueleto JSON das fotos ainda não fichadas, pronto para colar no config.

### 2. Limpar e tratar — `2_processar.py`

Para cada foto, na ordem: rotação (prints de foto deitada), apagamento do texto, retoque, enquadramento.

**Apagar texto.** Os retângulos de `apagar` são reconstruídos com [LaMa](https://github.com/enesmsahin/simple-lama-inpainting), que refaz o fundo em vez de borrar. Funciona bem inclusive sobre parede, madeira, papel e fundo desfocado.

> Prefira sempre tirar o texto **pelo enquadramento** (`ancora`) a apagá-lo. O corte não inventa pixel nenhum. Na prática, texto no topo ou no rodapé do story quase sempre sai no corte 4:5; o inpainting fica para o texto que caiu no meio da foto.

**Retoque.** Discreto por princípio, para a foto continuar parecendo o registro que o cliente fez:

- dominante de cor estimada pelos pixels claros e pouco saturados da cena (papel, embalagem, parede), com força limitada;
- exposição levada a um alvo pelo percentil 95, com teto de ±0,3 EV;
- ponto de preto real, curva S suave, vibrance só no que está apagado, clareza local, vinheta de 2% e uma passada leve de nitidez.

Todos os valores estão em `retoque` no config.

**Enquadrar.** Corte na proporção do feed (padrão 4:5, 1080x1350) usando `ancora` como posição da janela: em foto em pé é o topo do corte, em foto deitada é a margem esquerda. É esse número que decide o que entra e o que fica de fora.

### 3. Publicações — `3_publicacoes.py`

Monta as pastas de cada post com as fotos na ordem das páginas (o @ do autor vai no nome do arquivo) e escreve `legenda.txt` com as hashtags no fim. Também gera um `LEGENDAS.md` com tudo junto.

### 4. Prévia de aprovação — `4_preview.py`

Uma página HTML única no formato do feed do Instagram: carrossel navegável, contador, bolinhas, o @ do autor marcado em cada slide e a legenda exatamente como vai ser publicada. No lugar do número de curtidas aparece o crédito das fotos, para não inventar métrica em material de aprovação. Tem botão de tela cheia e atalho `F`.

## Uso

```bash
pip install -r requirements.txt
mkdir prints && cp ~/seus-prints/*.PNG prints/
cp config.exemplo.json config.json

python3 1_recortar.py          # olhe saida/_arrobas.png e saida/_reguas/ e preencha o config
python3 2_processar.py         # ~1 min por foto com inpainting, poucos segundos sem
python3 3_publicacoes.py
python3 4_preview.py && open saida/preview/index.html
```

Para reprocessar uma foto só depois de ajustar a ficha dela:

```bash
python3 2_processar.py --somente IMG_0002
```

## Conduzindo com um agente

Três decisões da etapa 1 dependem de ver a imagem: ler o @, medir os retângulos de texto e escolher o enquadramento. É exatamente o tipo de tarefa que um agente com visão (Claude Code, por exemplo) faz bem a partir de `_arrobas.png` e `_reguas/`. O [AGENTS.md](AGENTS.md) traz o roteiro pronto.

## Antes de publicar as fotos

O material é de terceiros. Marcar a marca em um story não é, por si só, autorização para republicar a foto no feed: confirme com o cliente qual é a política dele, e redobre o cuidado quando aparecerem crianças ou pessoas identificáveis que não são a autora do story. O crédito com o @ é o mínimo, não o suficiente.

## Requisitos

- Python 3.10+
- Pillow, NumPy e `simple-lama-inpainting` (`requirements.txt`)
- O modelo big-lama (~200 MB) é baixado sozinho no primeiro uso com `apagar` preenchido, e fica em `~/.cache/torch`

## Licença

MIT
