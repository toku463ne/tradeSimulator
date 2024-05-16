WITH r AS (
    SELECT
        a.codename,
        dt,
        (h+l+c)/3 as price,
        v,
        RANK() OVER (PARTITION BY date_trunc('month', dt) 
    ORDER BY v DESC) as rank
    FROM 
        ohlcv_mo1 AS a
), m1 AS (
    SELECT
        codename,
        dt,
        (h+l+c)/3 as price,
        v
    FROM
        ohlcv_mo1
    WHERE
        codename not like '^%'
        and codename not in ('1357.T', '1570.T')
), m2 AS (
    SELECT
        codename,
        dt,
        (h+l+c)/3 as price,
        v
    FROM
        ohlcv_mo1
    WHERE
        codename not like '^%'
        and codename not in ('1357.T', '1570.T')
) 
select r.codename, r.dt, r.price, m2.price-r.price as price_diff, r.v-m1.v as v_diff 
from r
join m1 on r.codename = m1.codename AND date_trunc('month', r.dt) = date_trunc('month', m1.dt- interval '1 month')
join m2 on r.codename = m2.codename AND date_trunc('month', r.dt) = date_trunc('month', m2.dt+ interval '1 month')
WHERE
    rank <= 10
ORDER BY
    dt, rank;
    
    