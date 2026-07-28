# Roteiro para agente

As etapas 1, 3 e 4 são mecânicas. O trabalho de verdade é preencher o `config.json`, e ele depende de **olhar** as imagens. Este é o roteiro.

## 1. Rodar a etapa 1 e ler os @

```bash
python3 1_recortar.py
```

Abra `saida/_arrobas.png`. É uma pilha de cabeçalhos ampliados 3x, **na ordem alfabética dos arquivos** (a etapa imprime a ordem no terminal).

O @ errado é o pior defeito possível aqui: marca outra pessoa na legenda. Então:

- amplie mais (5x a 8x) qualquer nome com `i`, `l`, `1`, `0`, `o`, `rn` ou underscore no fim;
- para contar underscores, compare a largura do traço com a de um underscore isolado de outro nome: dois underscores dão exatamente o dobro;
- na dúvida entre dígito e letra, o `1` desta fonte tem uma bandeirinha no topo e o `l` é uma barra reta.

Anote cada @ na ficha correspondente.

## 2. Medir texto e enquadramento

Abra cada `saida/_reguas/<nome>.jpg`. As linhas rosa marcam 10% na horizontal, as ciano 5% na vertical.

Para cada foto, decida nesta ordem:

1. **A foto está deitada?** Se sim, `rot: -90` (gira no sentido horário) ou `90`. Depois de rodar a etapa 1, gere uma régua da imagem já rotacionada antes de medir o resto.
2. **Dá para tirar o texto no corte?** A janela 4:5 tem 74,7% da altura de um story 9:16, então `ancora` pode ir de 0 a ~0,253. Se o texto está no topo, comece o corte abaixo dele; se está no rodapé, comece mais acima. Prefira sempre isso a apagar.
3. **Sobrou texto no meio?** Aí sim entre com um retângulo em `apagar`, com uma folga de 1 a 2% em volta das letras. Adesivos de reação (corações, GIFs) contam como texto.
4. **O corte respeita o assunto?** O prato, a embalagem ou o rosto precisam caber inteiros. Vale perder um pedaço do fundo, não do assunto.

## 3. Conferir o resultado

```bash
python3 2_processar.py
```

Olhe `saida/3_final/`. Duas checagens que pegam quase tudo:

- monte uma folha de contato com todas as fotos e procure texto sobrando;
- monte uma tira só com os 16% de cima e os 16% de baixo de cada foto, que é onde ficam os overlays que escapam do corte.

Reprocesse foto a foto com `--somente NOME` até limpar. Se o ajuste for de retoque, enquadramento ou selo, use `--reusar-limpo` para não repetir o inpainting.

## 4. Agrupar e escrever legenda

Junte as fotos por tema (mesma cena, mesmo prato, mesmo clima), não por ordem de arquivo, e ponha a foto mais forte como primeira página, que é a capa do carrossel. Cada post credita seus autores na legenda.

```bash
python3 3_publicacoes.py && python3 4_preview.py && open saida/preview/index.html
```

## Não faça

- Não invente número de curtidas, alcance ou qualquer métrica na prévia: é material de aprovação.
- Não publique a pasta `prints/` nem `saida/` em repositório: são fotos de terceiros.
- Não aumente os parâmetros de `retoque` para "melhorar" a foto. O alvo é parecer a mesma foto, bem resolvida, e não uma foto filtrada.
