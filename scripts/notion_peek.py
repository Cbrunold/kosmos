"""Look at any Notion database the integration can see, by title.

    python3 scripts/notion_peek.py nobel            # data sources whose title contains "nobel"
    python3 scripts/notion_peek.py "content creator" --rows 5

Prints each match's id, schema (property name → type, select options), row
count, and the first few rows flattened — enough to write a seed or a diff
against a database whose shape is not known in advance. Read-only.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, query_all  # noqa: E402
from fetch_all import flatten  # noqa: E402


def find_all(query: str) -> list:
    d = call("POST", "https://api.notion.com/v1/search",
             {"query": query, "filter": {"property": "object", "value": "data_source"}, "page_size": 100})
    out = []
    for r in d.get("results", []):
        title = "".join(x.get("plain_text", "") for x in r.get("title", [])).strip()
        if query.lower() in title.lower():
            out.append((title, r["id"]))
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    query = sys.argv[1]
    nrows = int(sys.argv[sys.argv.index("--rows") + 1]) if "--rows" in sys.argv else 3
    hits = find_all(query)
    if not hits:
        print(f"no data source with {query!r} in its title is visible to the integration")
        return
    for title, ds_id in hits:
        ds = call("GET", f"https://api.notion.com/v1/data_sources/{ds_id}")
        print(f"\n== {title}   {ds_id}")
        for name, spec in ds["properties"].items():
            extra = ""
            if spec["type"] in ("select", "multi_select", "status"):
                opts = [o["name"] for o in spec[spec["type"]].get("options", [])]
                extra = "  " + ", ".join(opts[:12]) + (" …" if len(opts) > 12 else "")
            print(f"   {name:32} {spec['type']}{extra}")
        rows = query_all(ds_id)
        print(f"   -- {len(rows)} rows; first {min(nrows, len(rows))}:")
        for p in rows[:nrows]:
            row = {k: v for k, v in flatten(p).items() if k not in ("id", "url", "lastEdited") and v not in (None, [], "")}
            print("   ", json.dumps(row, ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
