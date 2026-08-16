"""Turn Natural Earth's 110m land polygons into one SVG path for the mines map.

    python3 scripts/make_basemap.py [path/to/ne_110m_land.geojson]

Downloads the GeoJSON if no path is given (public domain, from the
natural-earth-vector repo), projects it with a plain equirectangular
projection onto a 1000 × 500 canvas (x = lon + 180, y = 90 − lat, both × 1000/360),
rounds to one decimal, and writes web/land-110m.svgpath — a single `d`
attribute the mines page inlines. Vertices closer than 0.35 canvas units
(~125 km) to the previous kept vertex are dropped, which loses nothing at
the size the map is drawn and roughly halves the file.

Run once; the output is committed. Re-run only if the projection changes.
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson"
W, H = 1000, 500
MIN_STEP = 0.35


def project(lon, lat):
    return (lon + 180) * W / 360, (90 - lat) * H / 180


def ring_to_path(ring):
    pts = []
    last = None
    for lon, lat in ring:
        x, y = project(lon, lat)
        if last is not None and abs(x - last[0]) < MIN_STEP and abs(y - last[1]) < MIN_STEP:
            continue
        pts.append((x, y))
        last = (x, y)
    if len(pts) < 3:
        return ""
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if src and src.exists():
        g = json.loads(src.read_text())
    else:
        print("downloading", URL)
        g = json.load(urllib.request.urlopen(URL))
    parts = []
    n_in = n_out = 0
    for f in g["features"]:
        geom = f["geometry"]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for poly in polys:
            for ring in poly:
                n_in += len(ring)
                p = ring_to_path(ring)
                if p:
                    parts.append(p)
                    n_out += p.count("L") + 1
    out = ROOT / "web" / "land-110m.svgpath"
    out.write_text("".join(parts))
    print(f"{n_in} -> {n_out} vertices, {len(parts)} rings, {out.stat().st_size:,} bytes -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
