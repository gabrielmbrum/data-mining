# mineração de dados da FIPE

## abstract

Este trabalho investigará as dinâmicas temporais de depreciação de veículos automotores a partir do *dataset* [fipeX](https://www.fipex.com.br), com foco no impacto da inserção de veículos elétricos (EVs) no mercado brasileiro frente aos modelos convencionais a combustão. Metodologicamente, o estudo abordará três questões centrais: (i) a verificação de assimetrias estatísticas nas taxas de depreciação entre elétricos e à combustão de mesma faixa de valor; (ii) a análise de co-movimento de preços entre elétricos e à combustão; e (iii) a avaliação comparativa entre a clusterização em séries temporais 1D tradicionais e representações bidimensionais geradas via *Gramian Angular Field* (GAF) e *Markov Transition Field* (MTF). A proposta visa unir a caracterização econômica de novos ativos à exploração de representações visuais/espaciais como estratégia de transformação de atributos em tarefas não supervisionadas de mineração de dados.

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

### inserção e depreciação dos carros elétricos

Gautam, P.; Pode, G.; Pode, R.; Ayetor, G.K.; Diouf, B. **Depreciation in the Electric Vehicle Transition: Sustainability of the Second-Hand Electric Vehicle Market**. 2024. [link](https://www.mdpi.com/2624-8921/6/4/101).

Schloter, L. **Empirical analysis of the depreciation of electric vehicles compared to gasoline vehicles**. 2022. [link](https://www.sciencedirect.com/science/article/pii/S0967070X22002074?casa_token=wLwhHOvENXEAAAAA:mspiqOmDbnIZueiv70QtPZ0kvpkXcfXO5GPpvgd-b6cSlvCiZdvqh49ci7vwKyykq_PK4RXS7Uk).

Silva, R. F. **Avaliação do impacto de barreiras para adoção de veículos elétricos na cidade de São Paulo**. 2024. [link](http://bibliotecatede.uninove.br/handle/tede/3569).

Jair, U. J. **Análise de cenários da inserção de veículos elétricos em conjunto com geradores fotovoltaicos**. 2022. [link](https://repositoriocopia.utfpr.edu.br/jspui/handle/1/32786)

Alvarez, F. H. B. **Modelagem da Aceitação de Veículos Elétricos considerando Políticas de Incentivo, Consciência Ambiental, Inovação Pessoal e Auto-eficácia Financeira: uma Extensão ao UTAUT 2**. 2024. [link](https://www.maxwell.vrac.puc-rio.br/67544/67544.PDF)

### guerra de preços e impacto dos chineses

Changjun Li; Congmei Xu; Tongtong An; Mengcheng Yu; Xiangjian Xin. **The Global Electric Vehicle (EV) Industry Price War: Implications for Managerial Decision-Making**. 2026. [link](https://fieam.org/index.php/ojs/article/view/192).

Abrardi, L. **Market Structure and Competitive Dynamics of Electric Vehicle in Europe**. 2026. [link](https://webthesis.biblio.polito.it/39592/)

LI, Shanjun et al. *The rise of electric vehicles in China: Growth, challenges and future prospects*. **The Great Energy Transformation in China**, p. 109, 2025. [link](file:///home/brum/Documents/9781760467227.pdf)

### reshaping

Wu, J. **Imaging feature-based clustering of financial time series**. 2023. [link](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0288836)

Ulyanin, Stepan, Jose R. Vazquez-Canteli, and Zoltan Nagy. **Feature extraction and clustering of building energy profiles encoded as images**. 2019. [link](https://publications.ibpsa.org/proceedings/bs/2019/papers/BS2019_210896.pdf)

Jueco, Jayson C., et al. **Performance Analysis of Time Series-to-Image Encoding Across Different Clustering Methods for Labeling Anomalous Load Data in Selected Visayas Subgrids**. IEEE, 2024. [link](https://ieeexplore.ieee.org/abstract/document/11258841?casa_token=gY6rhy8hdx4AAAAA:qTlP4gcZshOo6G2TAgV-v02IkUm7gS712NJDB5hnF_eregtmzd1snrZV0rxDtelgwLJFwX9rjPo)
