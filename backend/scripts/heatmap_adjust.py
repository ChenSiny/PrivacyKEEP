#!/usr/bin/env python3
"""
Adjust heatmap weights in the SQLite database for demo purposes.

Default behavior is DRY-RUN (no changes). Use --apply to commit.

Examples:
  # Preview what would be changed around the auto-detected center
  python backend/scripts/heatmap_adjust.py --radius 2 --factor 0.7

  # Apply changes and create a timestamped backup
  python backend/scripts/heatmap_adjust.py --radius 2 --factor 0.7 --apply

You can also specify a manual center (x,y):
  python backend/scripts/heatmap_adjust.py --center 50,50 --radius 3 --factor 0.5 --apply
"""
import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from statistics import median

DEF_DB_PATH = (Path(__file__).resolve().parents[1] / 'sports_privacy.db')

def parse_center(s: str):
    try:
        x_str, y_str = s.split(',')
        return int(x_str), int(y_str)
    except Exception:
        raise argparse.ArgumentTypeError('center must be in format x,y (integers)')


def ensure_db(path: Path):
    if not path.exists():
        print(f"Database not found: {path}")
        sys.exit(2)


def find_auto_center(rows):
    # rows: list of tuples (id, anonymous_id, x, y, weight, created_at)
    xs = [r[2] for r in rows]
    ys = [r[3] for r in rows]
    if not xs or not ys:
        return 0, 0
    # median is robust to outliers
    return int(median(xs)), int(median(ys))


def select_rows(conn):
    try:
        cur = conn.execute("SELECT id, anonymous_id, x, y, weight, created_at FROM heatmap_data")
        return cur.fetchall()
    except sqlite3.OperationalError as e:
        if 'no such table' in str(e).lower():
            print('Table heatmap_data not found. Have you run the app and uploaded any heatmap data?')
        else:
            print('SQLite error:', e)
        sys.exit(3)


def backup_db(db_path: Path) -> Path:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = db_path.with_suffix(f'.db.bak.{ts}')
    shutil.copy2(db_path, bak)
    return bak


def main():
    parser = argparse.ArgumentParser(description='Adjust heatmap weights in SQLite database')
    parser.add_argument('--db', type=Path, default=DEF_DB_PATH, help='Path to SQLite DB (default: backend/sports_privacy.db)')
    parser.add_argument('--center', type=parse_center, default=None, help='Center as x,y (integers). Default: auto median of data')
    parser.add_argument('--radius', type=int, default=2, help='Radius (grid units) around center to adjust')
    parser.add_argument('--factor', type=float, default=0.7, help='Multiply weights by this factor in the target region')
    parser.add_argument('--apply', action='store_true', help='Apply changes (otherwise dry-run)')
    args = parser.parse_args()

    db_path: Path = args.db.resolve()
    ensure_db(db_path)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    rows = select_rows(conn)
    total = len(rows)
    if total == 0:
        print('No heatmap_data rows found.')
        sys.exit(0)

    cx, cy = args.center if args.center is not None else find_auto_center(rows)

    # Select target rows within radius (Manhattan distance or Chebyshev?) Use Chebyshev (square) for grid-like neighborhoods.
    def in_radius(r):
        return max(abs(r[2] - cx), abs(r[3] - cy)) <= args.radius

    targets = [r for r in rows if in_radius(r)]

    print(json.dumps({
        'db': str(db_path),
        'total_rows': total,
        'auto_center': args.center is None,
        'center': {'x': cx, 'y': cy},
        'radius': args.radius,
        'factor': args.factor,
        'targets': len(targets),
        'sample_before': [
            {'id': r[0], 'x': r[2], 'y': r[3], 'weight': r[4]}
            for r in targets[:10]
        ]
    }, ensure_ascii=False, indent=2))

    if not args.apply:
        print('\nDry-run only. Use --apply to commit changes.')
        return

    # Apply: backup then update
    bak = backup_db(db_path)
    print(f'Backup created: {bak}')

    cur = conn.cursor()
    updated = 0
    for r in targets:
        rid, _, x, y, w, _ = r
        new_w = round(w * args.factor, 6)
        cur.execute("UPDATE heatmap_data SET weight = ? WHERE id = ?", (new_w, rid))
        updated += 1
    conn.commit()

    # Show a small diff sample after
    rows_after = select_rows(conn)
    targets_after = [row for row in rows_after if max(abs(row[2]-cx), abs(row[3]-cy)) <= args.radius]

    print(json.dumps({
        'updated_rows': updated,
        'sample_after': [
            {'id': r[0], 'x': r[2], 'y': r[3], 'weight': r[4]}
            for r in targets_after[:10]
        ]
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
