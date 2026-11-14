# Roteiro Completo de Apresentação de Slides (12 Minutos)
**Projeto:** Caracterização de Padrões de Depreciação Automotiva sob a Transição Energética  
**Autor:** Gabriel Martins Brum | UNESP — Mineração de Dados  
**Distribuição de Tempo:**  
- **Introdução:** 3 min (já realizada previamente)  
- **Fundamentação Teórica:** 2 min (Slides 1 e 2)  
- **Materiais e Métodos:** 2.5 min (Slides 3 e 4)  
- **Resultados e Discussão:** 3.5 min (Slides 5, 6 e 7)  
- **Conclusão:** 1 min (Slide 8)  
- **Tempo Restante das Seções:** **9 minutos** (Total da Apresentação: **12 minutos**)

---

## Estrutura Geral dos 8 Slides (9 Minutos)

```
[00:00 - 03:00] INTRODUÇÃO (Contexto, Problema e Questões de Pesquisa) [3 min]
─────────────────────────────────────────────────────────────────────────────
[03:00 - 04:00] SLIDE 1: Fundamentação I — Reshaping: Séries Temporais em Imagens 2D
[04:00 - 05:00] SLIDE 2: Fundamentação II — Espaços Latentes e Agrupamento
─────────────────────────────────────────────────────────────────────────────
[05:00 - 06:15] SLIDE 3: Materiais — Base fipeX, Amostragem e VRR
[06:15 - 07:30] SLIDE 4: Métodos — Pipeline de Transformação e Protocolo Experimental
─────────────────────────────────────────────────────────────────────────────
[07:30 - 08:45] SLIDE 5: Resultados I — Eficácia das Representações (GASF vs. 1D vs. DTW)
[08:45 - 10:00] SLIDE 6: Resultados II — Os 4 Arquétipos e Concentração dos Elétricos
[10:00 - 11:00] SLIDE 7: Discussão — Diagnóstico Causal: Combustível vs. Preço
─────────────────────────────────────────────────────────────────────────────
[11:00 - 12:00] SLIDE 8: Conclusão — Respostas às Hipóteses, Contribuições e Futuro
```

---

# BLOCO 1: FUNDAMENTAÇÃO TEÓRICA (2 min)

### Slide 1: Reshaping Temporal: Séries em Matrizes de Imagens 2D
* **Tempo sugerido:** 1 min [03:00 → 04:00]
* **Objetivo:** Justificar a transição do espaço vetorial 1D para o espaço de textura 2D.
* **Layout do Slide:** Duas colunas (Equações e conceito à esquerda; Imagem à direita).

#### Conteúdo em Tela:
1. **Limitações do 1D Clássico:**
   * Distância Euclidiana impõe sincronismo rígido ponto a ponto ($t_i \leftrightarrow t_i$).
   * *Dynamic Time Warping* (DTW) tem alto custo quadrático ($O(N^2 \cdot T^2)$) e mascara choques macroeconômicos síncronos da safra.
2. **Abordagem de Wang & Oates (2015):**
   * Mapeamento polar bijetor sem perda de informação temporal:
     $$\phi_t = \arccos(\tilde{x}_t), \quad r_t = \frac{t}{T}, \quad \tilde{x}_t \in [0, 1]$$
   * **GASF (Gramian Angular Summation Field):**
     $$\mathrm{GASF} = [\cos(\phi_i + \phi_j)] = \tilde{X}^T \tilde{X} - \sqrt{I - \tilde{X}^2}^T \sqrt{I - \tilde{X}^2}$$
     * A diagonal principal preserva os valores originais; fora da diagonal captura correlações temporais relativas.
3. **Elemento Visual:** [`examples_fuel.png`](file:///home/brum/pos-graduacao/mineracao-de-dados/projeto/docs/artigo/img/examples_fuel.png) (comparando a série 1D com o heatmap de GASF, GADF e MTF para elétrico, híbrido e gasolina).

> **Fala Sugerida (60s):**  
> *"Ao analisar séries temporais de depreciação, o alinhamento euclidiano rígido falha ao capturar nuances, enquanto o DTW, além de ser computacionalmente custoso, deforma choques macroeconômicos síncronos de mercado. Para contornar isso, adotamos o método de Wang e Oates, convertendo cada série temporal em uma matriz quase-definida de Gram. Como o cosseno é bijetor no intervalo [0, 1], o valor reescalonado vira o ângulo e o tempo vira o raio. Como vemos na figura à direita, uma trajetória de queda acentuada em um elétrico gera uma assinatura visual única de cores frias na matriz GASF, preservando correlações cruzadas e a informação original na diagonal principal."*

---

### Slide 2: Espaços Latentes, Agrupamento e Critérios de Validação
* **Tempo sugerido:** 1 min [04:00 → 05:00]
* **Objetivo:** Explicar a compressão com PCA e a mecânica do K-Means e métricas de validação.
* **Layout do Slide:** 3 blocos conceituais.

#### Conteúdo em Tela:
1. **Redução Dimensional (PCA):**
   * Imagens $32 \times 32$ geram $1.024$ atributos por canal com alta colinearidade.
   * Projeção PCA retendo $95\%$ de variância acumulada: remove ruído de alta frequência e comprime o espaço.
2. **Modelagem de Agrupamento:**
   * **K-Means (Baseado em Centróides):** Minimização do SSE via K-Means++:
     $$\mathrm{SSE} = \sum_{k=1}^K \sum_{x \in C_k} \|x - m_k\|^2$$
   * **DBSCAN (Baseado em Densidade):** Linha de base para identificação de geometrias arbitrárias e detecção de ruído.
3. **Métrica Intrínseca Principal — Coeficiente de Silhueta ($s$):**
   $$s(i) = \frac{b(i) - a(i)}{\max(a(i),\, b(i))}, \quad s \in [-1, +1]$$
   *(Mede o balanço entre coesão intra-cluster $a(i)$ e isolamento inter-cluster $b(i)$).*

> **Fala Sugerida (60s):**  
> *"A matriz 2D resulta em 1.024 variáveis altamente simétricas. Para extrair apenas o sinal estrutural, aplicamos PCA preservando 95% da variância acumulada. No caso do GASF, isso condensa toda a dinâmica temporal em um espaço latente de apenas dois componentes ortogonais. Sobre esses espaços, aplicamos o algoritmo K-Means particional com K-Means++, além do DBSCAN para controle de densidade e ruído. Para avaliar formalmente a qualidade matemática dos agrupamentos sem usar rótulos cadastrais, o Coeficiente de Silhueta foi o critério decisor de coesão e separabilidade."*

---

# BLOCO 2: MATERIAIS E MÉTODOS (2.5 min)

### Slide 3: Materiais — Base de Dados FipeX e Preparação da Amostra
* **Tempo sugerido:** 1 min [05:00 → 06:00]
* **Objetivo:** Apresentar a fonte, critérios de inclusão, controle da Taxa de Retenção e estratos.
* **Layout do Slide:** Cards com números de impacto + Tabela resumida de classes.

#### Conteúdo em Tela:
1. **Filtros e Amostragem:**
   * Base pública FipeX ($9{,}28$ milhões de registros, $2001$ a $2026$).
   * Automóveis de passeio lançados a partir de **2019** ($\textit{ano\_modelo} \ge 2019$).
   * Janela temporal homogênea e contínua de **$T = 32$ meses** ($2{,}6$ anos de mercado).
   * Interpolação linear permitida até $10\%$ de faltantes (séries com lacuna $>10\%$ descartadas).
2. **Taxa de Retenção de Valor (VRR):**
   $$\mathrm{VRR}_{i,t} = \frac{P_{i,t}}{P_{i,0}} \quad (\text{Ancorada em } 100\% \text{ no mês } 0)$$
   * Normalização global com corte: $\tilde{x} = \mathrm{VRR} / 1{,}5 \in [0, 1]$.
3. **Distribuição Amostral ($N = 4.457$ trajetórias):**
   * **Flex:** $1.756$ ($39{,}4\%$) | **Gasolina:** $1.258$ ($28{,}2\%$) | **Diesel:** $871$ ($19{,}5\%$)
   * **Híbridos:** $382$ ($8{,}6\%$) | **Elétricos (BEV):** $190$ ($4{,}3\%$)
4. **Estratos de Preço de Lançamento ($P_0$):**
   * *Entrada:* $\le \text{R\$ } 83\text{k}$ | *Intermediário:* $\text{R\$ } 83\text{k} \text{ a } 325\text{k}$ | *Luxo:* $> \text{R\$ } 325\text{k}$

> **Fala Sugerida (60s):**  
> *"Extraímos da base histórica FipeX 4.457 trajetórias completas de automóveis lançados entre 2019 e 2026 com exatos 32 meses de acompanhamento contínuo. Esse recorte temporal é cirúrgico: captura a maturação de seminovo da frota eletrificada pós-pandemia. Para eliminar a escala monetária, calculamos a Taxa de Retenção de Valor (VRR) ancorada no preço de lançamento como 100%. A amostra contempla todos os combustíveis e segmenta os veículos pelos quartis de preço de entrada, criando as faixas de Entrada, Intermediário e Luxo."*

---

### Slide 4: Métodos — Pipeline Experimental e Espaços Comparados
* **Tempo sugerido:** 1.5 min [06:00 → 07:30]
* **Objetivo:** Mostrar o fluxo metodológico completo e a matriz experimental de comparação.
* **Layout do Slide:** Fluxograma do pipeline + Tabela de espaços latentes.

#### Conteúdo em Tela:
1. **Fluxo Metodológico:**  
   `Dados FIPE` $\rightarrow$ `VRR (32m)` $\rightarrow$ `Imagens (GASF/GADF/MTF)` $\rightarrow$ `PCA 95%` $\rightarrow$ `K-Means (K=2 a 7)` $\rightarrow$ `Validação Intrínseca/Extrínseca`
2. **Matriz de Espaços Experimentais:**
   * **1D Euclidiano:** Vetores brutos em $\mathbb{R}^{32}$.
   * **1D DTW:** *Dynamic Time Warping* com centróides iterativos por DBA.
   * **2D GASF + PCA:** Redução de $1.024 \rightarrow$ **2 componentes** ($96{,}8\%$ variância explicada).
   * **2D GADF + PCA:** Redução para **5 componentes** ($95{,}2\%$).
   * **2D MTF + PCA:** Redução para $532$ componentes ($95{,}0\%$).
3. **Protocolo de Validação:**
   * *Intrínseco:* Silhueta e Davies-Bouldin para determinar o melhor $K$.
   * *Extrínseco:* Aderência a combustível e preço via ARI, NMI e $V$ de Cramér.
   * *Inferencial:* ANOVA Two-Way ($2 \times 5$) sobre a variação líquida aos 32 meses ($\Delta \mathrm{VRR}_{32m}$).

> **Fala Sugerida (90s):**  
> *"Nosso protocolo experimental colocou frente a frente cinco espaços de dados. Como linhas de base clássicas, avaliamos o vetor unidimensional euclidiano e o DTW com centróides DBA. Para o domínio bidimensional, calculamos as matrizes GASF, GADF e MTF de dimensão 32 por 32. Aplicando o PCA, observamos uma taxa de compressão extraordinária: o GASF precisou de apenas 2 componentes principais para reter quase 97% da variância das curvas! Cada uma dessas representações foi testada no K-Means com K variando de 2 a 7 com dez repetições independentes. Por fim, definimos um modelo de ANOVA bidirecional cruzando combustível e estrato de preço para isolar formalmente o efeito da transição energética sobre o valor residual."*

---

# BLOCO 3: RESULTADOS E DISCUSSÃO (3.5 min)

### Slide 5: Eficácia das Representações (A Vitória do GASF + PCA)
* **Tempo sugerido:** 1 min [07:30 → 08:30]
* **Objetivo:** Apresentar a superioridade de agrupamento e de velocidade computacional.
* **Layout do Slide:** Gráfico de linha da Silhueta à esquerda; Tabela de métricas e conclusões à direita.

#### Conteúdo em Tela:
* **Tabela de Comparação de Desempenho para $K=4$:**

| Abordagem | Silhueta ($s$) $\uparrow$ | Davies-Bouldin ($DB$) $\downarrow$ | Tempo de Execução $\downarrow$ |
| :--- | :---: | :---: | :---: |
| **2D GASF + PCA** | **0,410** | **0,784** | **0,05 s** |
| 2D GADF + PCA | 0,424 | 0,967 | 0,05 s |
| 1D Euclidiano | 0,311 | 1,028 | 0,06 s |
| 1D DTW (DBA) | 0,243 | 1,212 | 71,62 s |
| 2D MTF + PCA | 0,064 | 3,116 | 0,80 s |

* **Conclusões Técnicas:**
  * O espaço **GASF elevou a Silhueta em 32%** frente ao vetor 1D ($0,410$ vs. $0,311$).
  * O **GASF foi $1.400\times$ mais rápido que o DTW** ($0,05$s contra $71,62$s).
  * O **MTF falhou ($s=0,064$)**, confirmando que a discretização em quantis remove a sensibilidade a magnitudes de desvalorização contínua.
* **Elemento Visual:** [`silhouette_comparison.png`](file:///home/brum/pos-graduacao/mineracao-de-dados/projeto/docs/artigo/img/silhouette_comparison.png).

> **Fala Sugerida (60s):**  
> *"O primeiro grande resultado metodológico é a validação da hipótese de representação. Como exposto no gráfico e na tabela, a partição ótima ocorre em K=4. O espaço GASF reduzido via PCA alcançou o melhor coeficiente de silhueta (0,410) e o menor índice Davies-Bouldin (0,784), superando amplamente tanto o vetor 1D euclidiano quanto o DTW. Além disso, o ganho computacional foi impressionante: o processamento sobre o espaço latente GASF foi mil e quatrocentas vezes mais rápido que o alinhamento temporal DTW, viabilizando mineração em larga escala sem perda de separabilidade."*

---

### Slide 6: Arquétipos de Depreciação e o Destino dos Elétricos
* **Tempo sugerido:** 1.25 min [08:30 → 09:45]
* **Objetivo:** Apresentar a morfologia dos 4 clusters descobertos e a concentração dos elétricos.
* **Layout do Slide:** Figura com as 4 trajetórias em cima; Tabela de caracterização dos arquétipos embaixo.

#### Conteúdo em Tela:
* **Caracterização dos 4 Arquétipos ($K=4$, GASF + PCA):**

| Cluster | Perfil Temporal | Volume N (\%) | $\mathbf{\Delta VRR_{32m}}$ | \% dos Elétricos | \% dos Híbridos |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **$C_1$** | Valorização Moderada | $1.005$ ($22{,}5\%$) | $+23{,}3\%$ | $6{,}3\%$ | $14{,}4\%$ |
| **$C_2$** | **Depreciação Acelerada** | **$1.624$ ($36{,}4\%$)** | **$-13{,}6\%$** | **65,8%** | **48,4%** |
| **$C_3$** | Super-Valorização | $338$ ($7{,}6\%$) | $+39{,}6\%$ | **0,0%** | $0{,}5\%$ |
| **$C_4$** | Estabilidade | $1.490$ ($33{,}4\%$) | $+5{,}7\%$ | $27{,}9\%$ | $36{,}6\%$ |

* **Evidências Empíricas:**
  * **$65{,}8\%$ de todos os veículos elétricos** da base foram agrupados em $C_2$ (Depreciação Acelerada).
  * **Nenhum veículo elétrico ($0{,}0\%$)** ingressou no cluster de Super-Valorização ($C_3$).
  * Baixo alinhamento trivial com rótulos cadastrais ($ARI = 0,012$, $V = 0,140$): o modelo agrupou pela dinâmica temporal real e não por rótulo pré-estabelecido.
* **Elemento Visual:** [`archetypes_trajectories_2d_gasf.png`](file:///home/brum/pos-graduacao/mineracao-de-dados/projeto/docs/artigo/img/archetypes_trajectories_2d_gasf.png).

> **Fala Sugerida (75s):**  
> *"Ao examinar a semântica dos 4 clusters formados, emergiram quatro arquétipos bem definidos. Note-se o contraste violento de mercado: enquanto veículos a combustão experimentaram uma valorização nominal atípica decorrente da crise de insumos pós-2020 (Clusters C1 e C3), os veículos 100% elétricos apresentaram um comportamento totalmente segregado. Quase 66% de todos os veículos elétricos do Brasil foram capturados no Cluster C2 de Depreciação Acelerada, e absolutamente nenhum elétrico atingiu o grupo de Super-Valorização. Os testes de concordância externa como ARI e V de Cramér foram baixos, provando que o algoritmo aprendeu dinâmicas reais das curvas em vez de simplesmente reproduzir categorias cadastrais."*

---

### Slide 7: Diagnóstico Causal: Combustível vs. Preço e Discussão
* **Tempo sugerido:** 1.25 min [09:45 → 11:00]
* **Objetivo:** Refutar a hipótese de viés econômico e discutir os 3 fatores da depreciação dos elétricos.
* **Layout do Slide:** Dois blocos lado a lado (ANOVA + Pareamento no Luxo à esquerda; Discussão de Mercado à direita).

#### Conteúdo em Tela:
1. **Decomposição por ANOVA Bidirecional ($2 \times 5$):**
   * **Tipo de Combustível:** $SS = 142.704$ ($F = 89{,}51, p = 2{,}8 \times 10^{-73}$).
   * **Estrato de Preço:** $SS = 73.614$ ($F = 92{,}34, p = 5{,}1 \times 10^{-40}$).
   * $\rightarrow$ A tecnologia de propulsão explica **o dobro da variabilidade** frente ao patamar de preço!
2. **Controle Intra-Estrato no Segmento de LUXO ($> \text{R\$ } 325.000$):**
   * **Elétrico de Luxo:** mediana de **$-23{,}8\%$** de depreciação.
   * **Gasolina de Luxo:** mediana de **$+1{,}2\%$** (valorização residual).
   * **Diesel de Luxo:** mediana de **$+12{,}1\%$**.
   * $\rightarrow$ **Defasagem líquida de 25 pontos percentuais** entre elétricos e combustão no mesmo nível de preço!
3. **Discussão dos Três Fatores de Mercado:**
   * *Degradação de Bateria:* incerteza sobre custos de reposição no pós-garantia.
   * *Guerra de Preços:* redução agressiva nos zero-km (BYD/GWM) desvalorizando seminovos.
   * *Rápida Obsolescência Técnica:* aumento célere de autonomia e velocidade de recarga.

> **Fala Sugerida (75s):**  
> *"Chegamos à questão crítica do trabalho: os elétricos desvalorizam mais porque são elétricos ou simplesmente porque 93% deles custam mais de 150 mil reais e carros de luxo desvalorizam mais? A ANOVA bidirecional e o pareamento intra-estrato respondem com clareza: a matriz energética explica quase o dobro da variabilidade da depreciação em comparação ao estrato de preço. Quando isolamos apenas o estrato de Luxo — comparando veículos de patamar similar acima de R$ 325 mil —, o modelo a gasolina valorizou +1,2% enquanto o elétrico perdeu -23,8%. Essa defasagem de 25 pontos percentuais comprova que a desvalorização decorre da motorização. Na prática, o comprador de seminovos teme a degradação e o custo de troca da bateria, enquanto a intensa guerra de preços das montadoras chinesas nos zero-quilômetro acelerou a queima do valor residual dos seminovos comprados antes."*

---

# BLOCO 4: CONCLUSÃO (1 min)

### Slide 8: Conclusão, Contribuições e Trabalhos Futuros
* **Tempo sugerido:** 1 min [11:00 → 12:00]
* **Objetivo:** Fechar a apresentação respondendo diretamente às duas questões de pesquisa, apontando contribuições e limitações.
* **Layout do Slide:** Duas colunas (Respostas às Questões à esquerda; Contribuições e Futuro à direita).

#### Conteúdo em Tela:
1. **Respostas às Questões de Pesquisa:**
   * **Q1 (Domínio Automotivo):** A desvalorização acelerada decorre prioritariamente da **propulsão elétrica** e não do estrato econômico, com **defasagem de 25 p.p.** frente a veículos a combustão pareados no mesmo estrato de luxo.
   * **Q2 (Mineração de Dados):** A codificação **GASF + PCA** superou significativamente os baselines 1D, elevando o coeficiente de Silhueta de $0{,}311$ para **$0{,}410$** e reduzindo o tempo de convergência em **três ordens de grandeza frente ao DTW** ($1.400\times$).
2. **Contribuições Principais:**
   * Primeira caracterização empírica em microdados da FIPE sobre a desvalorização na transição energética brasileira.
   * Validação da codificação matricial 2D para análise eficiente de séries de retenção de valor.
3. **Limitações e Trabalhos Futuros:**
   * Horizonte fixado em $32$ meses (limitação da safra recente de BEVs no país).
   * Próximos passos: monitorar o ciclo de fim de garantia de baterias (8 anos) e os impactos do Programa Mover e recomposição de alíquotas de importação.

> **Fala Sugerida (60s):**  
> *"Para concluir, este estudo responde a duas perguntas fundamentais. Em termos de domínio automotivo, provamos estatisticamente que a desvalorização acelerada é orientada pela matriz de propulsão elétrica e não pelo preço do veículo, com uma defasagem de 25 pontos percentuais no estrato de luxo. Em termos de mineração de dados, demonstramos que transformar séries temporais em matrizes GASF com redução via PCA não apenas eleva a separabilidade dos agrupamentos como elimina o gargalo computacional do DTW com aceleração de mil e quatrocentas vezes. Como trabalhos futuros, pretendemos monitorar o ciclo de expiração da garantia de 8 anos das baterias e o impacto da recomposição de impostos sobre a taxa de retenção. Muito obrigado e fico à disposição para as perguntas da banca."*

---

## Tabela de Gestão de Tempo Durante a Apresentação

| Marcador no Cronômetro | Slide em Apresentação | Ação do Apresentador |
| :---: | :--- | :--- |
| **00:00 - 03:00** | *Introdução & Contexto* | Falar de mobilidade elétrica, FIPE e apresentar as 2 QPs |
| **03:00 - 04:00** | Slide 1: Reshaping 1D $\rightarrow$ 2D | Apontar a fórmula polar e a imagem `examples_fuel.png` |
| **04:00 - 05:00** | Slide 2: Espaços Latentes e Silhueta | Destacar PCA com 2 componentes e fórmula da Silhueta |
| **05:00 - 06:00** | Slide 3: Amostragem e VRR | Enfatizar os 4.457 carros, 32 meses e os 190 elétricos |
| **06:00 - 07:30** | Slide 4: Pipeline Metodológico | Mostrar o fluxo de ponta a ponta e a ANOVA |
| **07:30 - 08:30** | Slide 5: Vitória do GASF + PCA | Apresentar Silhueta $0,410$ e a velocidade $1.400\times$ vs DTW |
| **08:30 - 09:45** | Slide 6: Os 4 Arquétipos | Destacar os $65,8\%$ dos elétricos em Depreciação Acelerada |
| **09:45 - 11:00** | Slide 7: Causalidade e Discussão | Apresentar o gap de 25 p.p. no luxo e os 3 fatores de mercado |
| **11:00 - 12:00** | Slide 8: Conclusão | Responder às 2 QPs, pontuar contribuições e fechar |
