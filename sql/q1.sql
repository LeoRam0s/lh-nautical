-- Q1: Quantidade total de linhas
select count(*) as quantidade_total_linhas from orders;

--Q1: Quantidade total de colunas
SELECT count(*) as total_colunas
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'orders';

-- Q1: Intervalo de datas analisado (data mínima e máxima)
select min(o.created_at ::date) as data_minima, max(o.created_at::date) as data_maxima from orders o;

-- Q1: Valor maximo, minimo e medio coluna total
select max(o.total) as total_maximo, min(o.total) as total_minimo, round(avg(o.total),2) as total_medio from orders o;