# LH Nautical

Projeto desenvolvido para análise dos dados da **LH Nautical**, contemplando exploração dos dados, consultas SQL, previsão de vendas, recomendação de produtos, construção da camada Gold e dashboard em Power BI.

## Estrutura do projeto

```text
lh-nautical/
├── dashboard/
├── data/
│   ├── 1-lh_nautical_csv/
│   └── 2-lh_nautical_gold/
├── notebooks/
├── scripts/
├── sql/
├── .env.example
├── compose.yaml
├── requirements.txt
└── schema.sql
```

### `dashboard/`

Contém o dashboard final desenvolvido no Power BI:

```text
dashboard_lh_nautical.pbix
```

### `data/`

Contém os dados utilizados no projeto.

```text
data/
├── 1-lh_nautical_csv/
└── 2-lh_nautical_gold/
```

* `1-lh_nautical_csv/`: dados originais disponibilizados para o desafio.
* `2-lh_nautical_gold/`: dados tratados e modelados para utilização no Power BI.

A camada Gold contém dimensões, fatos e tabelas auxiliares, como:

```text
dim_customer.csv
dim_date.csv
dim_employee.csv
dim_location.csv
dim_product.csv

fact_orders.csv
fact_order_items.csv
fact_returns.csv
fact_return_items.csv

aux_loyal_categories.csv
aux_loyal_customers.csv
aux_recommendations.csv
```

### `notebooks/`

Notebooks utilizados para análise e transformação dos dados.

```text
1-eda.ipynb
2-sales-forecast.ipynb
3-product-recommendation.ipynb
4-dashboard-gold-layer.ipynb
```

* `1-eda.ipynb`: análise exploratória dos dados.
* `2-sales-forecast.ipynb`: previsão de vendas.
* `3-product-recommendation.ipynb`: recomendação de produtos.
* `4-dashboard-gold-layer.ipynb`: construção da camada Gold utilizada no dashboard.

### `sql/`

Consultas SQL desenvolvidas durante o desafio.

```text
q1.sql
q4.sql
q5.sql
```

Os arquivos contêm consultas de exploração dos dados, análise de clientes e construção/análise da dimensão de datas.

### `scripts/`

Contém os scripts responsáveis pela criação do banco e carregamento dos CSVs no PostgreSQL.

#### `generate_sql_schema.py`

Analisa os arquivos presentes em:

```text
data/1-lh_nautical_csv/
```

e gera automaticamente o arquivo:

```text
schema.sql
```

O script identifica os tipos das colunas dos CSVs e cria os respectivos comandos `CREATE TABLE`.

Para executar:

```bash
python scripts/generate_sql_schema.py
```

#### `load_csv_to_postgres.py`

Responsável por carregar todos os CSVs para o PostgreSQL.

O script:

1. verifica se `schema.sql` existe;
2. gera o schema automaticamente caso não exista;
3. executa o `schema.sql` no PostgreSQL;
4. percorre os CSVs de `data/1-lh_nautical_csv/`;
5. cria/carrega a tabela correspondente a cada CSV;
6. verifica registros que já foram carregados;
7. insere somente os registros restantes;
8. interrompe a execução caso os dados já existentes sejam incompatíveis com o CSV.

Para executar:

```bash
python scripts/load_csv_to_postgres.py
```

## Configuração

### 1. Clone o projeto

```bash
git clone https://github.com/LeoRam0s/lh-nautical.git
cd lh-nautical
```

### 2. Crie o ambiente Python

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

As principais dependências utilizadas pelos scripts são:

* `psycopg`;
* `python-dotenv`.

## PostgreSQL com Docker

O projeto utiliza PostgreSQL através do Docker Compose.

### 1. Crie o arquivo `.env`

Copie o arquivo de exemplo:

macOS/Linux:

```bash
cp .env.example .env
```

Windows:

```powershell
copy .env.example .env
```

O arquivo deve possuir:

```env
POSTGRES_DB=lh_nautical
POSTGRES_USER=lh_nautical
POSTGRES_PASSWORD=123456
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
```

Você pode alterar usuário, senha e nome do banco.

Para executar os scripts Python localmente, mantenha:

```env
POSTGRES_HOST=localhost
```

A porta configurada no `.env` deve ser a mesma utilizada para acessar o PostgreSQL pelo computador.

### 2. Suba o PostgreSQL

Com Docker Desktop em execução:

```bash
docker compose up -d
```

Verifique o container:

```bash
docker compose ps
```

Se quiser acompanhar os logs:

```bash
docker compose logs -f postgres
```

Por padrão, o PostgreSQL ficará disponível em:

```text
Host: localhost
Porta: 5433
Banco: lh_nautical
Usuário: lh_nautical
```

## Carregando os dados

Com o PostgreSQL iniciado e o ambiente Python configurado:

```bash
python scripts/load_csv_to_postgres.py
```

Não é obrigatório executar `generate_sql_schema.py` antes.

Caso `schema.sql` não exista, o próprio script de carga irá gerá-lo.

O fluxo completo pode ser executado com:

```bash
docker compose up -d
python scripts/load_csv_to_postgres.py
```

## Encerrando o banco

Para parar os containers:

```bash
docker compose down
```

Para também remover os dados persistidos do PostgreSQL:

```bash
docker compose down -v
```

> `docker compose down -v` apaga o volume do PostgreSQL e, consequentemente, os dados armazenados no banco.
