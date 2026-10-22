from fastapi import FastAPI, UploadFile, File, HTTPException
import gpxpy
import psycopg
from psycopg.rows import dict_row

app = FastAPI()
DB_DSN = "host=localhost dbname=route_db user=route_user password=ваш_пароль"


@app.post("/upload")
async def upload_gpx(file: UploadFile = File(...)):
    if not file.filename.endswith(".gpx"):
        raise HTTPException(status_code=400, detail="Нужен файл .gpx")

    contents = await file.read()
    try:
        gpx = gpxpy.parse(contents.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка парсинга GPX: {e}")

    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                points.append((p.latitude, p.longitude, p.elevation, p.time))

    if not points:
        raise HTTPException(status_code=400, detail="В файле нет точек трека")

    name = gpx.tracks[0].name if gpx.tracks and gpx.tracks[0].name else file.filename

    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "INSERT INTO tracks (name) VALUES (%s) RETURNING id",
                (name,),
            )
            track_id = cur.fetchone()["id"]

            cur.executemany(
                """
                INSERT INTO track_points (track_id, lat, lon, elevation, time)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [(track_id, lat, lon, elev, t) for lat, lon, elev, t in points],
            )
        conn.commit()

    return {"track_id": track_id, "name": name, "points": len(points)}
