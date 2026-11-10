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
