# mineração de dados da FIPE

## abstract

Este trabalho investiga as dinâmicas temporais de depreciação de veículos automotores a partir do dataset fipeX, com foco no impacto da inserção de veículos elétricos (EVs) no mercado brasileiro frente aos modelos convencionais a combustão. Metodologicamente, o estudo aborda três questões centrais: (i) a verificação de assimetrias estatísticas nas taxas de depreciação entre elétricos e combustão pareados por faixa de valor nominal; (ii) a análise de co-movimento e efeitos de transbordamento de preços entre os segmentos; e (iii) a avaliação comparativa entre a clusterização em séries temporais 1D tradicionais e representações bidimensionais geradas via Gramian Angular Field (GAF) e Markov Transition Field (MTF). A proposta visa unir a caracterização econômica de novos ativos à exploração de representações visuais/espaciais como estratégia de transformação de atributos em tarefas não supervisionadas de mineração de dados.

<!-- baseando-se nos dados do *dataset* [fipeX](https://www.fipex.com.br), sendo extraídos pelo [huggingface](https://huggingface.co/datasets/joaosilva424/fipex-veiculos-brasil), irei investigar as seguintes questões de pesquisa:
1 - A inserção dos carros elétricos no mercado tem um desvalorização mais acentuada do que carros de mesma faixa de valores que consumem outras formas de combustíveis?
2 - A variação de preços dos carros elétricos necessariamente afeta o valor dos carros a combustão?
3 - A clusterização de arquétipos de desvalorização pode ser aprimorada utilizando reshaping, via GAF/MTF, para imagens?  -->

## introdução

### contextualização

O mercado automotivo global e brasileiro atravessa uma transição tecnológica impulsionada pela entrada acelerada de Veículos Elétricos (EVs). Diferente dos veículos a combustão interna (ICE), cujo comportamento de depreciação histórica é consolidado e linearizado pela idade do bem, os modelos eletrificados introduzem variáveis de incerteza operacional: degradação acelerada de baterias, rápida obsolescência tecnológica, políticas tarifárias voláteis e guerras de preços.

### motivações

Compreender e segmentar essas trajetórias temporais não é apenas uma demanda mercadológica de precificação e análise de risco para seguradoras e instituições financeiras; constitui um problema clássico de Data Mining voltado à mineração de séries temporais (time-series mining) e descoberta de padrões em dados ordenados. Métodos convencionais frequentemente achatam as curvas históricas ou dependem de distâncias euclidianas 1D que falham em capturar dinâmicas não-lineares, flutuações sazonais e correlações defasadas entre segmentos concorrentes.

<!-- os veículos são essencias para a sociedade moderna, influenciando diretamente ou indiretamente o dia a dia de toos. a compra dos mesmos envolvem várias razões, desde o início de novas formas de trabalho até realizações de sonhos. entretanto, a precificação dos mesmos se alteram por diversos fatores, sendo que a norma regulamentadora é a FIPE, em que realiza a tabularização de todos os modelos de veículos.  -->

### justificativa

A representação convencional de séries temporais como vetores unidimensionais impõe limitações analíticas severas ao processo de mineração de dados, restringindo os algoritmos de agrupamento a métricas de distância ponto a ponto altamente suscetíveis a ruídos, variações de escala e desalinhamentos temporais. Em dados ordenados complexos, como trajetórias de precificação de veículos, o tratamento vetorial tradicional desconsidera interações de vizinhança e estruturas não lineares inerentes às curvas de depreciação. Essa restrição metodológica fundamenta a necessidade de investigar transformações de atributos mais robustas, avaliando se representações bidimensionais geradas por Gramian Angular Fields (GAF) ou Markov Transition Fields (MTF) são capazes de codificar correlações cruzadas e dependências dinâmicas que escapam às distâncias euclidianas clássicas.  

Sob o ponto de vista da modelagem estatística e do aprendizado de máquina, o estudo se justifica ao contrapor a eficácia de espaços latentes extraídos dessas imagens frente a métodos tradicionais de redução de dimensionalidade e seleção de atributos. A aplicação de matrizes GAF/MTF permite transpor o problema de dados tabulares temporais para o domínio de operadores de extração de padrões espaciais, abrindo caminho para testar se técnicas de aprendizado não supervisionado se beneficiam da preservação topológica dessas transformações. Com isso, o trabalho estabelece um teste empírico controlado para mensurar se a complexidade adicional dessa projeção espacial se traduz, de fato, em clusters mais coesos e discriminantes do que os obtidos via abordagens vetoriais convencionais.  

Por fim, o trabalho preenche uma lacuna relevante na análise de fenômenos de mercado ao estruturar a descoberta de padrões de desvalorização e possíveis efeitos de transbordamento decorrentes da chegada dos veículos elétricos. Ao analisar o co-movimento de preços entre matrizes energéticas concorrentes, a pesquisa vai além do agrupamento meramente exploratório e fornece um protocolo experimental rigoroso baseado em técnicas consolidadas de pré-processamento, mitigação do impacto de outliers e validação de modelos. Dessa forma, a investigação entrega simultaneamente uma contribuição teórica sobre representação de dados ordenados na mineração de dados e uma ferramenta descritiva aplicada para precificação e gestão de risco sobre ativos automotivos. 

## objetivos

**Mapear e quantificar as taxas de depreciação dos veículos elétricos:** Mensurar a velocidade e amplitude da perda de valor dos modelos eletrificados em comparação direta a veículos a combustão pareados por porte, categoria e faixa de preço de lançamento.

**Avaliar o efeito de transbordamento (spillover) de marcas entrantes:** Analisar correlações temporais e possíveis quebras estruturais de preços em segmentos tradicionais após a introdução e guerra tarifária promovida por montadoras chinesas no mercado nacional.

**Implementar e validar o reshaping de séries temporais em imagens 2D:** Transformar as trajetórias unidimensionais de preços de cada veículo em representações matriciais utilizando algoritmos como Gramian Angular Field (GAF) ou Markov Transition Field (MTF).  

**Identificar e caracterizar arquétipos de desvalorização veicular:** Aplicar algoritmos de agrupamento (clustering) sobre representações vetoriais clássicas e sobre os espaços latentes gerados a partir das imagens, identificando perfis comportamentais típicos (alta retenção, desvalorização acelerada, valorização tardia).

**Comparar empiricamente a eficácia das representações:** Avaliar quantitativamente, por meio de métricas de qualidade de agrupamento (como coeficiente de Silhueta e índice Davies-Bouldin), se a transformação das séries para imagem supera as abordagens vetoriais unidimensionais tradicionais.

## cronograma

## referências