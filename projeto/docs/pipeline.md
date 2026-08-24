# overview

esse documento vai ser o histórico de ações realizadas, *insights* e métricas obtidos ao longo do tempo para facilitar a escrita final do artigo

os processos foram baseados no livro: **Introduction do Data Mining - 2nd Edition - TAN, Pang-Ning; STEINBACH, Michael; KARPATNE, Anuj; KUMAR, Vipin.**

---

## data quality

### measurement and data issues

##### measurement and data collection errors

*measurement error* é o erro de medida, onde o valor registrado difere do valor real. 

já o *data collection error* se refere ao erro de campos vazios ou inclusao de objetos que não pertencem ao domínio estudado. 

##### noise and artifacts

*noise* é um erro de medida aleatório. causa a perda do formato de dados espaciais/temporais, e em domínios mais comuns (imagens e sinais) existem formas de remover esses ruídos. porém, na maioria dos casos foca-se em criar algoritmos robustos que produzam resultados aceitáveis mesmo com *noise*.

*artifacts* é um erro causado por um fenômeno determinístico, onde consegue-se encontrar o motivador daquele "ruído", que então é chamado de artefato.

![noise](noise.png)

##### precision, bias and accuracy

>*precision:* proximidade entre medidas repetidas de mesma grandeza

>*bias:* variação sistemática das medições em relação à grandeza que está sendo medida

a precisão geralmente é medida pelo desvio padrão, já o bias pela diferença entre a média do conjunto e o valor conhecido da grandeza sendo medida (ex.: lab padrao mediu que a massa é 1g, porem a media das minhas medicoes é 1.001g, então o bias é de 0.001). 

>*accuracy:* proximidade das medidas ao valor verdadeiro da grandeza sendo medida.

os digítos significantes são importantes, onde a quantidade de dígitos deve seguir o limite dos instrumentos de medida utilizados, sem aumentar a precisão sem ter certeza do valor que se está assumindo.

#### outliers

são (i) instancias que tem características diferentes do restantes do conjunto ou (ii) valores de atributos que são incomuns de acordo com valores típicos do atributo. 

são referidos também como anomalias, porém não podem ser confundidos com ruído, onde pode ser dados legitimos que são interessantes em detectar.

#### missing values

a informação pode não ter sido coletada (ex.: alguem negou forneceu sua idade e peso), pode não ser aplicável para todos os objetos e vários outros motivos podem causar a falta de valores. há diversas maneiras para lidar com isso, como por exemplo:
- eliminar instâncias/atributo vazio
- estimando valores (interpolação)
- igmorar valores vazios (ex.: ao calcular a proximidade, não utilziar os campos vazios)

#### inconsistent values

ex.: CEP que não corresponde a cidade atribuída ao objeto. 

existem casos fáceis (altura e peso negativos), porém outros precisam ser consultados em fontes externas. 

#### duplicate data

pode ser duplicatas identicas ou quase identicas. os mesmos dados podem aparecer diversas vezes porem com nomes diferentes. os processos que resolvem isso são chamados de *deduplication*.

### issues related to applications

>"os dados são de alta qualidade se forem utilizados no contexto correto"

#### timeliness

dados que representam valores de determinado período de tempo podem não ter mais qualidade após o período ter passado.  

#### relevance

os dados precisam ter as informações necessárias para a aplicação, com um problema comum sendo o *sampling bias*, em que o recorte escolhido não representa o conjunto todo (perde-se proporções).

#### knowledge about the data

idealmente os conjuntos de dados tem sua documentação, assim possibilitando uma compreensão correta de seus atributos. 