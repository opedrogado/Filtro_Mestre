# Filtro Mestre — Ações B3

Acesse: https://filtromestre.streamlit.app/

Ferramenta pessoal para filtrar e analisar ações da B3. A ideia é juntar num lugar só os principais critérios que uso para avaliar ações valuation, ranking por estratégia, histórico de preços e dividendos sem depender de sites que cobram por isso.

## O que tem

**Filtros e Resultados**
Filtra ações por P/L, P/VP, DY, ROE, crescimento de receita e liquidez. Calcula automaticamente o Preço Justo de Graham e o Preço Teto de Barsi para cada ação. Quando a cotação está abaixo dos dois ao mesmo tempo, marca como 🎯 Dupla Margem.

**Ranking por estratégia**
Duas opções: Fórmula Mágica do Greenblatt (menor EV/EBIT + maior ROIC) ou Método das Estrelas do Primo Rico (pontua as top 3 em cada indicador). O simulador de carteira usa o ranking escolhido para distribuir o capital.

**Comparador**
Coloca até 3 ações lado a lado com todos os indicadores, destacando o melhor valor em cada linha.

**Simulador de Carteira**
Informa quanto quer investir, o app distribui proporcionalmente ao ranking, calcula quantas cotas inteiras dá pra comprar de cada ação, o troco que sobra e a projeção de dividendos anuais.

**Análise Histórica**
Para qualquer ação filtrada, mostra gráfico de preço dos últimos 5 anos com médias móveis de 50 e 200 dias (com sinalização de Golden/Death Cross), histórico completo de dividendos e um score de consistência baseado nos últimos anos de lucro e pagamento de proventos.

**Filtros Favoritos**
Salva configurações de filtro com nome para não precisar reconfigurar toda vez.

## Estrutura
├── app.py # interface e orquestração
├── dados.py # busca de dados (Fundamentus e Yahoo Finance)
├── calculos.py # valuation e ranking
└── favoritos.py # salvar/carregar filtros favoritos

## Rodando local

```bash
pip install -r requirements.txt
streamlit run app.py

## Observações
Dados do Fundamentus: cache de 4h
Dados históricos (Yahoo Finance): cache de 30min
filtros_favoritos.json é local e não vai pro Git — no Streamlit Cloud os favoritos não persistem entre deploys