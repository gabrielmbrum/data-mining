# Checklist de revisão: artigo de depreciação automotiva (fipeX)

## 1. Erros no relatório (main.tex)

### Legendas e figuras
- [ ] Legendas das Figuras 9 e 11 dizem "veículos de entrada", mas são dos segmentos intermediário e luxo.
- [ ] Legendas das Figuras 10 e 12 (YoY) também dizem "veículos de entrada".
- [ ] Legendas das Figuras 8, 10 e 12 estão com "Taxa de" sem complemento.
- [ ] Legenda da Figura 4 (YoY) diz "curvas de depreciação".
- [ ] Legenda da Figura 5 diz "com destaque para os quartis Q1 e Q3", mas a figura não tem esse destaque.
- [ ] Títulos das figuras em inglês e textos do relatório em português. Padronizar o idioma (títulos, eixos e legendas no matplotlib).
- [ ] Figura 6 mistura título em inglês com legendas em português ("Limite Entrada", "Início Luxo").
- [ ] Figura 5 usa lançamentos a partir de 2019, mas o texto não informa isso.

### Afirmações do texto
- [ ] Segmento intermediário: o texto diz que "nenhuma categoria obteve VRR acima de 100%", mas a Figura 9 mostra o Diesel em torno de 115%.
- [ ] Descrição do YoY diz "em relação ao preço no fim do ano anterior", mas a Equação 2 usa a média do ano anterior.
- [ ] Inflação: o pico de 12,13% é o IPCA acumulado em 12 meses de abril de 2022, não "a inflação do ano de 2022". Conferir o dado e a redação.
- [ ] Valores lidos nas figuras (VRR de 60%, 80%, -15% e outros) devem ser conferidos contra os números impressos pelo código.
- [ ] Texto de imputação de `ano_modelo` diz que só os ausentes foram preenchidos, mas o código sobrescreve todos os `zero_km == True`.

### Estrutura
- [ ] Resumo diz "três questões centrais" e a seção Objetivos lista cinco itens. Alinhar.
- [ ] Objetivo (ii), spillover de marcas chinesas, não é coberto por nenhuma atividade.
- [ ] Inserir tabela com o n de veículos únicos por segmento × combustível (a contagem já é impressa em `run_segmented_price_analysis`).
- [ ] Remover os comentários `% VERIFICAR` e `% INSERIR` do `main_revisado.tex` depois de resolvidos.
- [ ] Remover o `\newcommand{\p}` não usado (já removido no `main_revisado.tex`).

### Referências
- [ ] Anexar `references_adicionais.bib` ao `references.bib` e conferir os metadados (Wang & Oates, Sakoe & Chiba, Rousseeuw, Davies & Bouldin).
- [ ] IBGE (`ibge_ipca_2022`): trocar `url = {https://ibge.gov.br}` pelo link específico da divulgação do IPCA de abril de 2022.
- [ ] Schloter (2022) está citado para "métodos convencionais falham em capturar dinâmicas não lineares". O artigo é sobre depreciação de EVs, então trocar a fonte ou a afirmação.
- [ ] Alvarez (2024) está citado para "entrada acelerada de EVs no mercado". É uma tese de aceitação de EVs, então buscar fonte sobre o mercado brasileiro.
- [ ] Tan et al. (2019) está citado para "imputação baseada em conhecimento de domínio" e "múltiplos limiares". Conferir se o livro sustenta essas afirmações.
- [ ] Buscar fonte para a alta de preços de veículos em 2021–2022 (escassez de semicondutores, cadeia de suprimentos).

## 2. O que falta na AED (antes das Atividades 3 a 5)

- [ ] **n por segmento e combustível:** tabela de veículos únicos. Sem ela, as conclusões sobre elétricos e híbridos em "Entrada" não têm sustentação.
- [ ] **n por idade nas curvas de VRR:** mostrar o número de veículos em cada idade e definir um mínimo para plotar. Os saltos dos elétricos entre 80 e 100 meses parecem efeito de composição.
- [ ] **Incerteza:** bandas (IQR ou intervalo de confiança) ou mediana em vez de só a média.
- [ ] **Preços reais:** deflacionar valores, VRR e YoY pelo IPCA. Refazer a segmentação por Q1/Q3 com preços de lançamento deflacionados.
- [ ] **YoY robusto:** usar mediana ou média aparada, já que a média de percentuais é sensível a outliers.
- [ ] **Ano parcial de 2026:** tratar ou sinalizar (a média de 2026 compara um ano incompleto com um ano completo).
- [ ] **Primeiro ano do veículo:** o YoY do primeiro ano compara uma média parcial (lançamento no meio do ano) com um ano cheio.
- [ ] **Análise por marca:** linha do tempo de entrada de BYD, GWM e outras, para o objetivo (ii).
- [ ] **Spillover:** correlação cruzada entre séries de matrizes concorrentes e detecção de pontos de mudança (por exemplo, PELT) em torno da entrada das marcas chinesas.
- [ ] **Pareamento (matching):** pareamento de elétricos com equivalentes a combustão, previsto na Atividade 2 e ainda não feito.
- [ ] **Preparação para GAF/MTF:** definir comprimento mínimo das séries, tratamento de lacunas, comprimento uniforme (truncar ou reamostrar) e normalização por série.
- [ ] **Pico na idade 0 (Figura 2):** investigar por que há ~500 mil registros na idade 0 contra ~200 mil na idade 1.
- [ ] **Resumo e Objetivos:** alinhar o número de questões (ver seção 1).

## 3. Pontos do código a revisar (main.py)

### preprocess_data
- [ ] `ano_modelo` é sobrescrito para todos os registros com `zero_km == True`, não só para os ausentes. Ajustar com `pl.when(zero_km & ano_modelo.is_null())` ou ajustar o texto.
- [ ] Um carro 0 km e o mesmo ano-modelo na mesma data podem gerar registros duplicados em t=0 após a imputação. Rodar `check_multiple_t0_records` (comentado em `run_eda`).
- [ ] `data_lancamento` é o mínimo de `data_referencia` na base, que começa em 2005. Veículos anteriores a isso têm lançamento truncado (censura à esquerda).
- [ ] Remover `tipo_veiculo` e outras colunas só depois do filtro (já está assim, mas confirmar a ordem se o código for reorganizado).

### calculate_value_retention
- [ ] `group_by(cohort_keys).first()` sem ordenação pode escolher o preço de t=0 de forma arbitrária. Ordenar por `data_referencia` e consolidar duplicatas (por exemplo, média ou mínimo).
- [ ] Consolidar duplicatas por (veículo, `data_referencia`) antes de calcular a série, necessário para GAF/MTF.
- [ ] O `inner join` descarta veículos sem registro em `idade_meses == 0`. Imprimir quantos veículos e registros se perdem.

### plot_yoy_depreciation_by_calendar_year
- [ ] O YoY usa a média anual, e o `shift(1)` assume que o ano anterior existe. Se faltar um ano na série do veículo, o `shift` compara anos não consecutivos. Verificar se há lacunas.
- [ ] Trocar a média dos percentuais por mediana ou média aparada (ver AED).
- [ ] Ano parcial de 2026 (ver AED).

### run_segmented_price_analysis e analyze_price_brackets
- [ ] Q1/Q3 calculados sobre preços de lançamento nominais de 2019 a 2026. Deflacionar antes de segmentar.
- [ ] O filtro `ano_lancamento >= 2019` está duplicado em `analyze_price_brackets` e `run_segmented_price_analysis`. Centralizar em uma constante.
- [ ] Imprimir e salvar em arquivo a contagem de veículos únicos por segmento × combustível (para a tabela do relatório).

### Gráficos
- [ ] Padronizar idioma, tamanho de fonte e paleta de cores entre todas as figuras.
- [ ] Remover títulos dos gráficos (as legendas do LaTeX já descrevem) ou manter só em um idioma.
- [ ] `ax.set_ylim(top=150)` na Figura 3 e nas figuras por segmento corta o Diesel de entrada, que chega perto de 140%. Conferir se o teto cobre todos os dados.
- [ ] Marcar nos gráficos de VRR o número mínimo de veículos por idade (ver AED).

### Geral
- [ ] `2026 - max_age` fixa o ano no código. Usar `datetime.date.today().year` ou uma constante nomeada.
- [ ] Reativar em `run_eda` as funções comentadas necessárias para reproduzir os resultados do relatório (EDA completa), ou separar um script de relatório.
- [ ] Versionar os arquivos de saída (`output/`) e o `.parquet` de entrada com um README de reprodução.
