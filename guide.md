1
Запустить API: docker compose up --build
http://ваш_ip:8000/docs → POST /upload загрузить каждый файл
Записать соответствие файл -> track_id в блокнот
psql -h localhost -U route_user -d route_db -c "SELECT id, name FROM tracks;"
psql -h localhost -U route_user -d route_db -c "SELECT track_id, count(*) FROM track_points GROUP BY track_id;"

2
Для каждого track_id возьмите первую (или среднюю) точку трека.
Сохраните в track_weather
Код-шаблон сохранения (допишите в fetch_weather.py)
def save_weather(track_id, temperature, elevation, recorded_at):
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO track_weather (track_id, temperature, elevation, recorded_at) "
                    "VALUES (%s, %s, %s, %s);",
                    (track_id, temperature, elevation, recorded_at),
                )
    finally:
        conn.close()

3
analysis.py
Подключиться к БД, выгрузить track_points для трека в pandas.DataFrame.
Посчитайть: min_elevation, max_elevation, mean_elevation, std_elevation.
Частоту шагов оценить по расстоянию между точками - формула Haversine).
Сохранить в track_metrics.

4
описываем
истограмма — matplotlib.pyplot.hist(data, bins=30).
Мода, медиана, среднее, матожидание, skewness:
numpy.mean(data) — среднее
numpy.median(data) — медиана
scipy.stats.mode(data) — мода
scipy.stats.skew(data) — асимметрия
Матожидание для нормального распределения = среднее.

Проверка нормальности (стандартные тесты):
scipy.stats.shapiro(data) — тест Шапиро-Уилка.
scipy.stats.normaltest(data) — тест Д’Агостино (n > 5000).
scipy.stats.kstest(data, 'norm', args=(mean, std)) — Колмогоров-Смирнов.
Правило чтения: p-value > 0.05 -> нет оснований отвергнуть нормальность; p-value < 0.05 -> распределение не нормальное.
Записать гипотезу для каждого атрибута: высота распределена нормально / логнормально / бимодально
Где искать:
scipy.stats документация: docs.scipy.org/doc/scipy/reference/stats.html

5
кластерный анализ
Цель: разбить треки/точки на кластеры по атрибутам рельефа (высота, уклон, перепад)
Метрика качества sklearn.metrics.silhouette_score(X, labels)
сохрвнить в track_clusters

6
er диаграмма
Выгрузитт схему: pg_dump -h localhost -U route_user -d route_db --schema-only > schema_dump.sql.
диаграмму вручную в draw.io (app.diagrams.net) или dbdiagram.io
отметить таблицы, первичные ключи, внешние ключи, REFERENCES tracks(id)), типы полей.
Где искать:
dbdiagram.io

7
дэшборд
Matplotlib/Seaborn
Streamlit — самый быстрый способ(streamlit run app.py)
