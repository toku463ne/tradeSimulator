r AS (
    SELECT
        a.codename,
        dt,
        (h+l+c)/3 as price,
        RANK() OVER (PARTITION BY date_trunc('month', dt) 
    ORDER BY v DESC) as rank
    FROM 
        ohlcv_mo1 AS a
), m AS (
    SELECT
        codename,
        dt,
        (h+l+c)/3 as price,
    FROM
        ohlcv_d
    WHERE
        codename not like '^%'
        and codename not in ('1357.T', '1570.T')
    GROUP BY
        codename,
        date_trunc('month', dt)
) 