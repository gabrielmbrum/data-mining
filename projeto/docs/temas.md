## Opção 1: O "Efeito China" e a Curva de Depreciação de Eletrificados

**Título Sugerido:** Mineração de Dados e Análise Preditiva da Taxa de Depreciação de Veículos Elétricos e Híbridos no Mercado Automotivo Brasileiro

**Tema Central:** Avaliar se veículos de marcas entrantes (BYD, GWM) e eletrificados perdem valor mais rápido ou mais devagar do que modelos a combustão tradicionais (Toyota, VW, Chevrolet, Fiat) nos primeiros 12 a 36 meses.

**Técnicas de Mineração de Dados:**
- Regressão e Séries Temporais: Modelagem preditiva com LightGBM, XGBoost e CatBoost para estimar o valor residual após $N$ meses.
- Interpretabilidade (SHAP Values): Analisar a importância do tipo de combustível e da marca na velocidade da perda de valor.

**Engenharia de Atributos:** Criação de variáveis como $\text{Idade} = (\text{ano\_referencia} - \text{ano\_modelo})$, $\Delta\% \text{ Preço em 12 meses}$ e $\text{Razão Preço Usado / Preço 0km}$.

---

## Opção 2: Agrupamento de Perfis de Veículos por Comportamento de Desvalorização

**Título Sugerido:** Clusterização e Identificação de Arquétipos de Desvalorização Automotiva com Base na Tabela FIPE

**Tema Central:** Agrupar modelos de carros não pela categoria de marketing (SUV, Sedan, Hatch), mas sim pelo seu perfil real de curva de preço ao longo do tempo.

**Técnicas de Mineração de Dados:**
- Agrupamento (Clustering): K-Means, HDBSCAN ou Time-Series Clustering (usando Dynamic Time Warping - DTW).
- Redução de Dimensionalidade: PCA ou UMAP para visualização das trajetórias de desvalorização dos clusters.

**Contribuição do Artigo:** Identificar grupos que funcionam como "reserva de valor" versus grupos com desvalorização acelerada (ex.: luxo a combustão vs. elétrico de entrada).

---

## Opção 3: Detecção de Anomalias e Choques de Mercado

**Título Sugerido:** Detecção de Anomalias Temporais em Preços de Automóveis: Identificando Guerras de Preço e Choques Tributários

**Tema Central:** Identificar momentos em que montadoras aplicaram cortes agressivos de preços em modelos 0km ou em que mudanças de impostos (como o retorno gradual do imposto de importação para eletrificados) geraram quebras estruturais no mercado.

**Técnicas de Mineração de Dados:**
- Detecção de Anomalias: Isolation Forest, One-Class SVM ou Local Outlier Factor (LOF) aplicados à variação percentual mês a mês.
- Detecção de Ponto de Mudança (Change Point Detection): Algoritmos como PELT ou Ruptures nas trajetórias de preços.

---

## Opção 4: Regras de Associação e Correlação entre Segmentos

**Título Sugerido:** Mineração de Padrões e Efeitos de Transbordamento entre o Segmento de Eletrificados e Veículos a Combustão

**Tema Central:** Minerar como a variação de preço de modelos de topo chineses (ex: BYD Song Plus, Haval H6) afeta o comportamento e a precificação de concorrentes diretos a combustão (ex: Jeep Compass, Toyota Corolla Cross).

**Técnicas de Mineração de Dados:**
- Causalidade e Correlação Cruzada: Mineração de defasagens temporais (lagged correlation) e modelos de regressão multivariada.
- Árvores de Decisão e Regras de Regressão: Extração de regras interpretáveis do tipo: "Se o preço do SUV elétrico cair mais de X%, a probabilidade de queda do concorrente a combustão é Y%".