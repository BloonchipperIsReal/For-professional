import os

from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import gpxpy
import psycopg2
from psycopg2.extras import execute_values

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://route_user:geo927server552@localhost:5432/route_db",
)


def get_conn():
    return psycopg2.connect(DATABASE_URL)


@app.post("/upload")
async def upload_gpx(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        gpx = gpxpy.parse(contents.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка парсинга GPX: {e}")

    points = []
    track_name = None
    for track in gpx.tracks:
        if track_name is None:
            track_name = track.name
        for segment in track.segments:
            for p in segment.points:
                points.append((p.latitude, p.longitude, p.elevation, p.time))

    if not points:
        raise HTTPException(status_code=400, detail="В файле нет точек трека")

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tracks (name) VALUES (%s) RETURNING id;",
                    (track_name or file.filename,),
                )
                track_id = cur.fetchone()[0]

                execute_values(
                    cur,
                    "INSERT INTO track_points (track_id, lat, lon, elevation, time) VALUES %s",
                    [(track_id, lat, lon, elev, t) for lat, lon, elev, t in points],
                )
    finally:
        conn.close()

    return {"track_id": track_id, "points": len(points), "filename": file.filename}


@app.get("/tracks/{track_id}/gpx")
def get_track_gpx(track_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM tracks WHERE id = %s;", (track_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Трек не найден")
            track_name = row[0]

            cur.execute(
                "SELECT lat, lon, elevation, time FROM track_points "
                "WHERE track_id = %s ORDER BY time;",
                (track_id,),
            )
            points = cur.fetchall()
    finally:
        conn.close()

    if not points:
        raise HTTPException(status_code=404, detail="В треке нет точек")

    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack(name=track_name or f"track_{track_id}")
    gpx.tracks.append(gpx_track)
    segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(segment)

    for lat, lon, elev, t in points:
        segment.points.append(
            gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=lon, elevation=elev, time=t)
        )

    gpx_xml = gpx.to_xml()
    return Response(content=gpx_xml, media_type="application/gpx+xml")