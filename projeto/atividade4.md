# definição no relatório

Modelagem de agrupamento e extração de padrões aplicando algoritmos de \textit{clustering} (K-Means e abordagens baseadas em densidade) sobre as representações geradas por imagem e sobre os dados vetoriais clássicos. Para garantir uma validação robusta da abordagem bidimensional proposta, o projeto estabelecerá uma linha de base (\textit{baseline}) operando diretamente sobre as séries temporais unidimensionais (1D) da taxa de retenção de valor. Serão aplicadas medidas de similaridade clássicas, com ênfase na Distância Euclidiana e, principalmente, no algoritmo de \textit{Dynamic Time Warping} (DTW) \cite{sakoe1978dynamic}, que é especialista em alinhar defasagens temporais. O desempenho dos agrupamentos obtidos no espaço 1D com DTW servirá como parâmetro de controle crítico para avaliar o real ganho de informação e precisão proporcionado pelas codificações matriciais 2D (GAF e MTF).

# resumo de ações

1. agrupamento (k-means e abordagens baseadas em densidade) sobre os dados vetoriais clássicos
    - medidas de similaridade clássicas: distancia euclidiana e DTW 
2. agrupamento (=) sobre as representações geradas por imagens

# fundamentação de agrupamento

>fuzzy: cada ponto pertence a todos os clusters com um peso entre 0 e 1, sendo que a soma de todos os pesos é 1

## tipos de clusters

***well-separated clusters***
neste tipo cada cluster eh um conjunto de pontos que cada ponto dele esta mais proximo de todos os pontos dentro dele mesmo (cluster) do que qualquer ponto em outro cluster

***center-based***
conjunto de objetos que cada objeto em um cluster está mais próximo do centro de seu cluster do que qualquer outro centro de cluster

existem dois conceitos:
- *centróide*: média, ou mediana, de todos os pontos de um cluster
- *medoide*: ponto real do cluster que minimiza a distância total para os outros pontos

***contiguity-based***
cluster eh um conjunto de pontos que cada ponto está mais próximo de pelo menos um ponto em seu cluster do que qualquer outro ponto em qualquer outro cluster

dois objetos são conectados somente se estão dentro de uma determinada distância entre cada um

***density-based***
cada cluster eh uma região densa de pontos, que é separada por regiões de baixa densidadede de outras regiões de alta densidade

utilizado quando os clusters são irregulares e entrelaçados, e quando ruídos e outliers estão presentes

## k-means

K = n° de centróides

```pseudo
select K points as the initial centroids
REPEAT
    form K clusters by assigning all points to the closest centroid
    recompute the centroid of each cluster
UNTIL the centroids dont change
```

para selecionar o ponto mais próximo de cada centróide, precisamos de uma **medida de proximidade**

### funções de proximidade

distância de manhatann, distância euclidiana, correlação, similaridade de cosseno....

### função de erro

é a função que guia a direção do reposiocioanmento das centróides, onde busca-se minimizar a função de erro

a função mais comum é a *Sum of Squared Error* (SSE)

pagina 30

## validação de agrupamento

### validação intrínseca (não supervisionada)
- **coeficiente de silhueta (s):** mede o equilíbrio entre coesão intra-cluster e separação inter-cluster (Rousseeuw, 1987). Varia de -1 a +1.
- **índice davies-bouldin (DB):** razão média de dispersão interna pela separação entre centróides (Davies & Bouldin, 1979). Menor é melhor.

### validação extrínseca (concordância com ground truth)
- **adjusted rand index (ARI):** similaridade entre partições corrigida para chance (-1 a 1).
- **normalized mutual information (NMI):** informação mútua normalizada entre partição e classes externas (0 a 1).
- **homogeneidade e completude:** baseadas em entropia condicional.
- **v de cramér:** intensidade da associação nominal a partir de tabelas de contingência $\chi^2$.

---

# diagnóstico: o agrupamento identifica combustíveis ou faixas de valores?

### 1. métricas de validação externa (K=4)
- **combustível vs cluster:** ARI = 0.0117, NMI = 0.0217, Homog = 0.0213, Comp = 0.0222, Cramér's V = 0.1395
- **faixa de preço vs cluster:** ARI = 0.0121, NMI = 0.0239, Homog = 0.0270, Comp = 0.0214, Cramér's V = 0.1594

> Como as séries de VRR foram normalizadas na origem ($P_t / P_0$), a magnitude nominal do preço não direciona os grupos. As métricas com combustível e faixa de preço são equivalentes e baixas, provando que o agrupamento não é mero espelho de nenhum dos dois metadados, mas captura **arquétipos comportamentais** de dinâmica temporal.

### 2. decomposição da variância (ANOVA Two-Way)
Modelo: $\Delta VRR_{32m} \sim \text{Combustível} + \text{Faixa de Preço}$
- **Tipo de Combustível:** $SS = 142.703,9$ ($df=4, F=89,51, p = 2,80 \times 10^{-73}$)
- **Faixa de Preço:** $SS = 73.614,5$ ($df=2, F=92,34, p = 5,08 \times 10^{-40}$)

> O tipo de combustível explica **quase o dobro da variabilidade da depreciação** em relação à faixa de preço de lançamento.

### 3. concentração de elétricos e controle intra-faixa
- **Concentração Seletiva:** Mais de **55% dos elétricos** (espaço 1D) e **65,8%** (espaço 2D GASF) estão alocados no cluster de Depreciação Acelerada. No cluster de super-valorização pós-pandemia, os elétricos representam apenas 1,5% (ou 0% no 2D).
- **Controle Intra-Estrato (Luxo):**
  - Elétrico de Luxo: mediana de **-23,8%** (média de -20,0%)
  - Gasolina de Luxo: mediana de **+1,2%** (média de +5,4%)
  - Híbrido de Luxo: mediana de **-10,1%**
  - Diferença de mais de **25 pontos percentuais** dentro do mesmo segmento econômico de mercado.
- **Viés de Confundimento (Colinearidade):** 93,2% dos elétricos custavam acima de R$ 150k (Intermediário/Luxo, mediana R$ 322k), enquanto 75,5% dos Flex estão em Entrada (mediana R$ 77k). Não é o preço alto que faz o carro desvalorizar mais; são os eletrificados concentrados nos segmentos superiores que puxam a média para baixo.

