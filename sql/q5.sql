--Q5: Construa uma dimensão de datas utilizando sql
CREATE TABLE IF NOT EXISTS dim_date (
	date_key       INTEGER PRIMARY KEY,
    date           DATE NOT NULL UNIQUE,
    year           SMALLINT NOT NULL,
    day_of_year    SMALLINT NOT NULL,
    day_of_month   SMALLINT NOT NULL,
    day_of_week    SMALLINT NOT NULL,
    day_name       VARCHAR(20) NOT NULL,
    week_of_year   SMALLINT NOT NULL,
    month          SMALLINT NOT NULL,
    year_month     INTEGER NOT NULL,
    month_year     VARCHAR(20),
    month_name     VARCHAR(20) NOT NULL,
    quarter        SMALLINT NOT NULL,
    quarter_name   VARCHAR(5) NOT NULL,
    semester       SMALLINT NOT NULL,
    is_weekend     BOOLEAN NOT NULL
);

-- Popula dim_date
INSERT INTO dim_date (
    date_key,
    date,
    year,
    day_of_year,
    day_of_month,
    day_of_week,
    day_name,
    week_of_year,
    month,
    year_month,
    month_year,
    month_name,
    quarter,
    quarter_name,
    semester,
    is_weekend
)
SELECT
    TO_CHAR(calendar_date, 'YYYYMMDD')::integer AS date_key,
    calendar_date AS date,
    EXTRACT(YEAR FROM calendar_date)::smallint AS year,
    EXTRACT(DOY FROM calendar_date)::smallint AS day_of_year,
    EXTRACT(DAY FROM calendar_date)::smallint AS day_of_month,
    EXTRACT(ISODOW FROM calendar_date)::smallint AS day_of_week, -- Padrão ISO: segunda-feira = 1 e domingo = 7
    CASE EXTRACT(ISODOW FROM calendar_date)::integer
        WHEN 1 THEN 'Segunda-feira'
        WHEN 2 THEN 'Terça-feira'
        WHEN 3 THEN 'Quarta-feira'
        WHEN 4 THEN 'Quinta-feira'
        WHEN 5 THEN 'Sexta-feira'
        WHEN 6 THEN 'Sábado'
        WHEN 7 THEN 'Domingo'
    END AS day_name,
    EXTRACT(WEEK FROM calendar_date)::smallint AS week_of_year,
    EXTRACT(MONTH FROM calendar_date)::smallint AS month,
    (
        EXTRACT(YEAR FROM calendar_date)::integer * 100
        + EXTRACT(MONTH FROM calendar_date)::integer
    ) AS year_month,
    CASE EXTRACT(MONTH FROM calendar_date)::integer
        WHEN 1  THEN 'Janeiro'
        WHEN 2  THEN 'Fevereiro'
        WHEN 3  THEN 'Março'
        WHEN 4  THEN 'Abril'
        WHEN 5  THEN 'Maio'
        WHEN 6  THEN 'Junho'
        WHEN 7  THEN 'Julho'
        WHEN 8  THEN 'Agosto'
        WHEN 9  THEN 'Setembro'
        WHEN 10 THEN 'Outubro'
        WHEN 11 THEN 'Novembro'
        WHEN 12 THEN 'Dezembro'
    END
    || '/'
    || EXTRACT(YEAR FROM calendar_date)::integer AS month_year,
    CASE EXTRACT(MONTH FROM calendar_date)::integer
        WHEN 1  THEN 'Janeiro'
        WHEN 2  THEN 'Fevereiro'
        WHEN 3  THEN 'Março'
        WHEN 4  THEN 'Abril'
        WHEN 5  THEN 'Maio'
        WHEN 6  THEN 'Junho'
        WHEN 7  THEN 'Julho'
        WHEN 8  THEN 'Agosto'
        WHEN 9  THEN 'Setembro'
        WHEN 10 THEN 'Outubro'
        WHEN 11 THEN 'Novembro'
        WHEN 12 THEN 'Dezembro'
    END AS month_name,
    EXTRACT(QUARTER FROM calendar_date)::smallint AS quarter,
    (
        'Q'
        || EXTRACT(QUARTER FROM calendar_date)::integer
    )::varchar(5) AS quarter_name,
    CASE
        WHEN EXTRACT(MONTH FROM calendar_date) <= 6 THEN 1
        ELSE 2
    END::smallint AS semester,
    EXTRACT(ISODOW FROM calendar_date) IN (6, 7) AS is_weekend
FROM generate_series(
    DATE '2019-01-01',
    DATE '2027-12-31',
    INTERVAL '1 day'
) AS generated_dates(calendar_date)
ON CONFLICT (date_key) DO NOTHING;


--Q5: Cruze a dimensão de datas com a tabela de vendas para análise.
WITH limites AS (
    SELECT
        MIN(placed_at::date) AS data_inicial,
        MAX(placed_at::date) AS data_final
    FROM orders
),
vendas_diarias AS (
    SELECT
        placed_at::date AS data,
        SUM(COALESCE(total, 0)) AS valor_vendas
    FROM orders
    WHERE channel = 'pos'
    GROUP BY placed_at::date
),
media_por_dia_semana AS (
    SELECT
        d.day_of_week,
        d.day_name,
        COUNT(*) AS quantidade_dias_calendario,
        COUNT(*) FILTER (
            WHERE v.data IS NULL
        ) AS quantidade_dias_sem_venda,
        ROUND(
            AVG(COALESCE(v.valor_vendas, 0)),
            2
        ) AS media_vendas
    FROM dim_date AS d
    CROSS JOIN limites AS l
    LEFT JOIN vendas_diarias AS v
        ON v.data = d.date
    WHERE d.date BETWEEN l.data_inicial AND l.data_final
    GROUP BY
        d.day_of_week,
        d.day_name
)
SELECT
    day_name,
    quantidade_dias_calendario,
    quantidade_dias_sem_venda,
    media_vendas
FROM media_por_dia_semana
ORDER BY
    media_vendas ASC,
    day_of_week;

