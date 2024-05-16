WITH Stats AS (
    SELECT
        codename,
        date_trunc('month', dt) AS month,
        avg(v) AS mean,
        stddev(v) AS std_dev
    FROM
        ohlcv_d
    GROUP BY codename, date_trunc('month', dt)
), MonthlyRanked AS (
    SELECT
        a.codename,
        date_trunc('month', dt) AS month,
        ceil(avg(c)) as price,
        ceil(SUM(v)/1000000) AS total_volume_value,
        RANK() OVER (PARTITION BY date_trunc('month', dt) 
    ORDER BY SUM(v) DESC) as rank
    FROM 
        ohlcv_d AS a
    JOIN Stats on a.codename = Stats.codename 
           AND date_trunc('month', dt) = Stats.month
    WHERE
        v < Stats.mean + 3*Stats.std_dev
        and dt < '2018-01-01'
        and a.codename not like '^%'
        and a.codename not in ('1357.T', '1570.T')
    GROUP BY
        a.codename,
        date_trunc('month', dt)
    HAVING ceil(avg(c)) < 3001
), NextMonthC AS (
    SELECT
        codename,
        date_trunc('month', dt) AS month,
        ceil(avg(c)) as price
    FROM
        ohlcv_d
    WHERE
        dt < '2018-02-01'
        and codename not like '^%'
        and codename not in ('1357.T', '1570.T')
    GROUP BY
        codename,
        date_trunc('month', dt)
)
SELECT
    mr.codename,
    codes.name,
    mr.month,
    mr.price as curr_price,
    n.price as next_price,
    (n.price - mr.price) as diff,
    mr.total_volume_value
FROM
    MonthlyRanked as mr
LEFT JOIN codes on codes.codename = mr.codename
LEFT JOIN NextMonthC n ON mr.codename = n.codename AND date_trunc('month', n.month) = date_trunc('month', mr.month + interval '1 month')
WHERE
    rank <= 10
ORDER BY
    month, rank;