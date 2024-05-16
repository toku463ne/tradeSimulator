WITH r AS (
    SELECT
        a.codename,
        dt,
        RANK() OVER (PARTITION BY date_trunc('month', dt) 
    ORDER BY v DESC) as rank
    FROM 
        ohlcv_mo1 AS a
), p AS (
    SELECT 
        r.codename, 
        date_trunc('month', r.dt) as month, 
        ROUND(CAST(LEFT(CAST(p.price AS TEXT), 4) AS FLOAT) / 10) as grp
    FROM r
    LEFT join peaks_d_10 AS p on r.codename = p.codename
    WHERE
    p.dt < r.dt + interval '1 month'
    AND
    p.dt >= r.dt - interval '1 year'
)
select codename, month, grp, count(*) as cnt 
from p
where codename = '1301.T'
group by codename, month, g
having count(*) > 1

