#!/usr/bin/env python3
import sqlite3
import argparse
import shutil
import os
import tempfile

QUERY = """
SELECT
  datetime(time/1000000-11644473600,'unixepoch') AS timestamp,
  event_type,
  detail1,
  detail2
FROM (
  SELECT
    last_visit_time AS time,
    'BROWSING' AS event_type,
    url AS detail1,
    title AS detail2
  FROM urls
  WHERE last_visit_time > 0

  UNION ALL

  SELECT
    v.visit_time AS time,
    'VISIT' AS event_type,
    u.url AS detail1,
    u.title AS detail2
  FROM visits v
  JOIN urls u ON v.url = u.id

  UNION ALL

  SELECT
    d.start_time AS time,
    'DOWNLOAD_START' AS event_type,
    d.target_path AS detail1,
    u.url AS detail2
  FROM downloads d
  LEFT JOIN downloads_url_chains u ON d.id = u.id

  UNION ALL

  SELECT
    d.end_time AS time,
    'DOWNLOAD_END' AS event_type,
    d.target_path AS detail1,
    u.url AS detail2
  FROM downloads d
  LEFT JOIN downloads_url_chains u ON d.id = u.id
  WHERE d.end_time IS NOT NULL
)
ORDER BY time;
"""

def main():
    parser = argparse.ArgumentParser(
        description="Genera un timeline forense completo desde el archivo History de Chrome/Edge"
    )
    parser.add_argument(
        "-i", "--history",
        required=True,
        help="Ruta al archivo History (Chrome / Edge)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Archivo CSV de salida (opcional)"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.history):
        raise FileNotFoundError("El archivo History no existe")

    # Copia forense a archivo temporal (evita locks y alteraciones)
    tmp_dir = tempfile.mkdtemp()
    tmp_history = os.path.join(tmp_dir, "History")
    shutil.copy2(args.history, tmp_history)

    conn = sqlite3.connect(tmp_history)
    cursor = conn.cursor()
    cursor.execute(QUERY)
    rows = cursor.fetchall()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("timestamp,event_type,detail1,detail2\n")
            for r in rows:
                line = ",".join(
                    '"' + (str(x).replace('"', '""') if x else "") + '"' for x in r
                )
                f.write(line + "\n")
        print(f"[+] Timeline exportado a {args.output}")
    else:
        for r in rows:
            print(" | ".join(str(x) if x else "" for x in r))

    conn.close()

if __name__ == "__main__":
    main()


