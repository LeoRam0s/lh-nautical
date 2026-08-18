-- Observacao: Foi considerado uma venda valida apenas as que tiveram o status de paid


---- Q4: 1. Ticket medio e diversidade de categoras pra cada customer_id
WITH vendas_validas AS (
    SELECT o.id, o.customer_id, o.total
    FROM orders AS o
    WHERE o.status = 'paid'
),
metricas_clientes as (
	select 
		vv.customer_id,
		sum(vv.total) as faturamento_total,
		count(vv.id) as frequencia_transacoes,
		sum(vv.total) / count(vv.id) as ticket_medio
	from vendas_validas vv
	group by vv.customer_id
),
clientes_categorias as (
	select 
		vv.customer_id, 
		COUNT(DISTINCT p.category_id) as diversidade_categorias
	from vendas_validas vv
	inner join order_items oi on vv.id = oi.order_id
	inner join product_variants pv on pv.id = oi.product_variant_id
	inner join products p on p.id = pv.product_id
	inner join categories c on c.id = p.category_id
	group by vv.customer_id
)
select 
	mc.customer_id, mc.ticket_medio, cc.diversidade_categorias
from metricas_clientes  mc
join clientes_categorias cc on cc.customer_id = mc.customer_id 
order by mc.ticket_medio desc, mc.customer_id asc
;

---- Q4: 2. top 10 clientes que atende ao filtro de elite
WITH vendas_validas AS (
    SELECT o.id, o.customer_id, o.total
    FROM orders AS o
    WHERE o.status = 'paid'
),
metricas_clientes as (
	select 
		vv.customer_id,
		sum(vv.total) as faturamento_total,
		count(vv.id) as frequencia_transacoes,
		sum(vv.total) / count(vv.id) as ticket_medio
	from vendas_validas vv
	group by vv.customer_id
),
clientes_categorias as (
	select 
		vv.customer_id, 
		COUNT(DISTINCT p.category_id) as diversidade_categorias
	from vendas_validas vv
	inner join order_items oi on vv.id = oi.order_id
	inner join product_variants pv on pv.id = oi.product_variant_id
	inner join products p on p.id = pv.product_id
	inner join categories c on c.id = p.category_id
	group by vv.customer_id
),
filtro_elite_clientes as (
	select 
		mc.customer_id, 
		mc.ticket_medio,
		cc.diversidade_categorias
	from metricas_clientes mc 
	join clientes_categorias cc on cc.customer_id = mc.customer_id
	where cc.diversidade_categorias >= 13
	order by mc.ticket_medio desc, mc.customer_id asc
	limit 10
)
select 
	fec.customer_id, c.legal_name, fec.ticket_medio 
from filtro_elite_clientes fec
join customers c on c.id = fec.customer_id
order by fec.ticket_medio desc, fec.customer_id ASC
;

---- Q4: 3. Categoria de produto que concentra a maior quantidade total de itens comprados
WITH vendas_validas AS (
    SELECT o.id, o.customer_id, o.total
    FROM orders AS o
    WHERE o.status = 'paid'
),
metricas_clientes as (
	select 
		vv.customer_id,
		sum(vv.total) as faturamento_total,
		count(vv.id) as frequencia_transacoes,
		sum(vv.total) / count(vv.id) as ticket_medio
	from vendas_validas vv
	group by vv.customer_id
),
clientes_categorias as (
	select 
		vv.customer_id, 
		count(distinct c.name) as diversidade_categorias
	from vendas_validas vv
	inner join order_items oi on vv.id = oi.order_id
	inner join product_variants pv on pv.id = oi.product_variant_id
	inner join products p on p.id = pv.product_id
	inner join categories c on c.id = p.category_id
	group by vv.customer_id
),
filtro_elite_clientes as (
	select 
		mc.customer_id, 
		mc.ticket_medio,
		cc.diversidade_categorias
	from metricas_clientes mc 
	join clientes_categorias cc on cc.customer_id = mc.customer_id
	where cc.diversidade_categorias >= 13
	order by mc.ticket_medio desc, mc.customer_id asc
	limit 10
)
select 
	c.name as categoria, sum(oi.quantity) as quantidade_total_itens_comprados 
from filtro_elite_clientes fec
inner join vendas_validas vv on vv.customer_id = fec.customer_id
inner join order_items oi on oi.order_id = vv.id
inner join product_variants pv on pv.id = oi.product_variant_id
inner join products p on p.id = pv.product_id
inner join categories c on c.id = p.category_id
group by c.name
order by quantidade_total_itens_comprados desc
limit 1
;