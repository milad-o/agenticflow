"""CSV tools: merge two CSVs and validate a join.

- MergeCsvTool: join two CSVs on specified columns and write an output CSV.
- ValidateCsvJoinTool: validate that a merged CSV aligns with keys from the inputs (counts, missing keys).
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool


class MergeCsvTool(BaseTool):
    name: str = "merge_csv"
    description: str = (
        "Merge two CSV files into one by joining on specified columns. "
        "Args: left_path (str), right_path (str), left_on (str), right_on (str), how (str='inner'), output_path (str), encoding (str='utf-8')."
    )

    def _run(
        self,
        left_path: str,
        right_path: str,
        left_on: str,
        right_on: str,
        output_path: str,
        how: str = "inner",
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:  # type: ignore[override]
        left_p = Path(left_path)
        right_p = Path(right_path)
        out_p = Path(output_path)
        if not left_p.exists() or not right_p.exists():
            return {"error": "Input file(s) not found"}
        how = (how or "inner").lower()
        if how not in {"inner", "left", "right"}:
            return {"error": f"Unsupported join how='{how}' (supported: inner,left,right)"}

        try:
            with left_p.open("r", encoding=encoding, newline="") as lf:
                lreader = csv.DictReader(lf)
                left_rows = list(lreader)
                left_fields = lreader.fieldnames or []
            with right_p.open("r", encoding=encoding, newline="") as rf:
                rreader = csv.DictReader(rf)
                right_rows = list(rreader)
                right_fields = rreader.fieldnames or []

            # Build index for right on right_on
            r_index: Dict[str, List[Dict[str, Any]]] = {}
            for rr in right_rows:
                key = str(rr.get(right_on, ""))
                r_index.setdefault(key, []).append(rr)

            # Prepare output headers (avoid duplicate join key column from right side)
            right_fields_no_key = [f for f in right_fields if f != right_on]
            out_fields = left_fields + right_fields_no_key

            out_p.parent.mkdir(parents=True, exist_ok=True)
            merged_count = 0
            with out_p.open("w", encoding=encoding, newline="") as outf:
                writer = csv.DictWriter(outf, fieldnames=out_fields)
                writer.writeheader()
                if how in ("inner", "left"):
                    for lr in left_rows:
                        lkey = str(lr.get(left_on, ""))
                        matches = r_index.get(lkey, [])
                        if matches:
                            for rr in matches:
                                row = dict(lr)
                                for k, v in rr.items():
                                    if k == right_on:
                                        continue
                                    row[k] = v
                                writer.writerow(row)
                                merged_count += 1
                        elif how == "left":
                            # carry left row with blanks for right-only fields
                            row = dict(lr)
                            for k in right_fields_no_key:
                                row.setdefault(k, "")
                            writer.writerow(row)
                            merged_count += 1
                elif how == "right":
                    # Build index for left as well
                    l_index: Dict[str, List[Dict[str, Any]]] = {}
                    for lr in left_rows:
                        lkey = str(lr.get(left_on, ""))
                        l_index.setdefault(lkey, []).append(lr)
                    for rr in right_rows:
                        rkey = str(rr.get(right_on, ""))
                        matches = l_index.get(rkey, [])
                        if matches:
                            for lr in matches:
                                row = dict(lr)
                                for k, v in rr.items():
                                    if k == right_on:
                                        continue
                                    row[k] = v
                                writer.writerow(row)
                                merged_count += 1
                        else:
                            # right-only row
                            base = {f: "" for f in left_fields}
                            for k, v in rr.items():
                                if k == right_on:
                                    base[left_on] = v  # map right key to left key name
                                else:
                                    base[k] = v
                            writer.writerow(base)
                            merged_count += 1

            return {
                "output_path": str(out_p),
                "merged_rows": merged_count,
                "left_rows": len(left_rows),
                "right_rows": len(right_rows),
                "how": how,
                "left_on": left_on,
                "right_on": right_on,
            }
        except Exception as e:
            return {"error": str(e)}


class ValidateCsvJoinTool(BaseTool):
    name: str = "validate_csv_join"
    description: str = (
        "Validate a CSV join against input keys. "
        "Args: left_path (str), right_path (str), merged_path (str), left_on (str), right_on (str), encoding (str='utf-8')."
    )

    def _run(
        self,
        left_path: str,
        right_path: str,
        merged_path: str,
        left_on: str,
        right_on: str,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:  # type: ignore[override]
        try:
            def read_keys(path: str, key: str) -> List[str]:
                with Path(path).open("r", encoding=encoding, newline="") as f:
                    reader = csv.DictReader(f)
                    return [str(r.get(key, "")) for r in reader]

            lkeys = read_keys(left_path, left_on)
            rkeys = read_keys(right_path, right_on)
            mkeys = read_keys(merged_path, left_on)

            lset, rset, mset = set(lkeys), set(rkeys), set(mkeys)
            missing_from_left = sorted(list((rset - lset)))
            missing_from_right = sorted(list((lset - rset)))
            unmatched_in_merged = sorted(list((mset - (lset & rset))))

            return {
                "left_rows": len(lkeys),
                "right_rows": len(rkeys),
                "merged_rows": len(mkeys),
                "keys_left": len(lset),
                "keys_right": len(rset),
                "keys_merged": len(mset),
                "missing_from_left": missing_from_left,
                "missing_from_right": missing_from_right,
                "unmatched_in_merged": unmatched_in_merged,
                "ok": len(unmatched_in_merged) == 0,
            }
        except Exception as e:
            return {"error": str(e)}


class CsvChunkAggregateTool(BaseTool):
    name: str = "csv_chunk_aggregate"
    description: str = (
        "Compute grouped aggregations over a large CSV without loading it fully into memory. "
        "Args: path (str), group_by (str), value_column (str), agg (str='mean'), delimiter (str=','), encoding (str='utf-8'), top_n (int=50)."
    )


class PandasChunkAggregateTool(BaseTool):
    name: str = "pandas_chunk_aggregate"
    description: str = (
        "Compute grouped aggregations (mean) over a large CSV using pandas with chunked reads. "
        "Args: path (str), group_by (str), value_column (str), chunksize (int=100000), encoding (str='utf-8'), top_n (int=50)."
    )

    def _run(
        self,
        path: str,
        group_by: str,
        value_column: str,
        chunksize: int = 100000,
        encoding: str = "utf-8",
        top_n: int = 50,
    ) -> Dict[str, Any]:  # type: ignore[override]
        try:
            import pandas as pd  # type: ignore
        except Exception as e:
            return {"error": f"pandas not available: {e}"}
        p = Path(path)
        if not p.exists() or p.is_dir():
            return {"error": f"File not found or is a directory: {path}"}
        try:
            sums: Dict[str, float] = {}
            counts: Dict[str, int] = {}
            total_rows = 0
            for chunk in pd.read_csv(p, chunksize=int(chunksize) if chunksize and int(chunksize) > 0 else 100000, encoding=encoding):
                # ensure columns exist
                if group_by not in chunk.columns or value_column not in chunk.columns:
                    return {"error": f"Columns not found. group_by='{group_by}' value_column='{value_column}'. Headers={list(chunk.columns)}"}
                # coerce to numeric, errors to NaN, then dropna for computation
                vals = pd.to_numeric(chunk[value_column], errors='coerce')
                grp = chunk[group_by]
                df = pd.DataFrame({"_g": grp, "_v": vals}).dropna(subset=["_v", "_g"])
                if df.empty:
                    continue
                agg = df.groupby("_g")["_v"].agg(["sum", "count"]).reset_index()
                for _, row in agg.iterrows():
                    g = str(row["_g"])  # type: ignore[index]
                    s = float(row["sum"])  # type: ignore[index]
                    c = int(row["count"])  # type: ignore[index]
                    sums[g] = sums.get(g, 0.0) + s
                    counts[g] = counts.get(g, 0) + c
                total_rows += len(chunk)
            groups = []
            for k, c in counts.items():
                s = sums.get(k, 0.0)
                avg = (s / c) if c > 0 else 0.0
                groups.append({"group": k, "count": c, "sum": s, "average": avg})
            groups.sort(key=lambda x: (-x["count"], x["group"]))
            if top_n and top_n > 0:
                groups = groups[:top_n]
            return {
                "path": str(p),
                "group_by": group_by,
                "value_column": value_column,
                "agg": "mean",
                "row_count": total_rows,
                "unique_groups": len(counts),
                "groups": groups,
                "engine": "pandas",
            }
        except Exception as e:
            return {"error": str(e)}

    def _run(
        self,
        path: str,
        group_by: str,
        value_column: str,
        agg: str = "mean",
        delimiter: str = ",",
        encoding: str = "utf-8",
        top_n: int = 50,
    ) -> Dict[str, Any]:  # type: ignore[override]
        """
        Stream rows and compute per-group sum and count, then derive averages.
        Only returns top_n groups by count to keep payloads small.
        """
        import csv as _csv
        from collections import defaultdict
        p = Path(path)
        if not p.exists() or p.is_dir():
            return {"error": f"File not found or is a directory: {path}"}
        agg = (agg or "mean").lower()
        if agg not in {"mean", "avg", "average"}:
            return {"error": f"Unsupported agg='{agg}'. Only 'mean' supported."}
        sums: Dict[str, float] = defaultdict(float)
        counts: Dict[str, int] = defaultdict(int)
        total_rows = 0
        try:
            with p.open("r", encoding=encoding, newline="") as f:
                reader = _csv.DictReader(f, delimiter=delimiter)
                if group_by not in (reader.fieldnames or []) or value_column not in (reader.fieldnames or []):
                    return {"error": f"Columns not found. group_by='{group_by}' value_column='{value_column}'. Headers={reader.fieldnames}"}
                for row in reader:
                    total_rows += 1
                    key = str(row.get(group_by, ""))
                    try:
                        val = float(str(row.get(value_column, "") or 0))
                    except Exception:
                        # skip non-numeric values for aggregation
                        continue
                    sums[key] += val
                    counts[key] += 1
            groups = []
            for k, c in counts.items():
                s = sums.get(k, 0.0)
                avg = (s / c) if c > 0 else 0.0
                groups.append({"group": k, "count": c, "sum": s, "average": avg})
            # sort by count desc
            groups.sort(key=lambda x: (-x["count"], x["group"]))
            if top_n and top_n > 0:
                groups = groups[:top_n]
            return {
                "path": str(p),
                "group_by": group_by,
                "value_column": value_column,
                "agg": "mean",
                "row_count": total_rows,
                "unique_groups": len(counts),
                "groups": groups,
            }
        except Exception as e:
            return {"error": str(e)}
