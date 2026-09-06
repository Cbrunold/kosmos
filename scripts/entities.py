"""A page for every entity: /equations/pythagorean-theorem, /people/rudolf-diesel,
/cosmos/obs-mauna-kea-observatory, /elements/fe — one static file each, in both languages.

Until 2026-09-06 these URLs were answered by server.js rewriting the section page's head;
a crawler saw twenty shelves with fourteen hundred names. Now each entity is its own page:
every property of its Notion row (long text as prose, lists as chips, relations resolved
to links to the other entities' pages), a "referenced by" section computed from every
other table's relations, the link to its card on the shelf where the interactive context
lives, and its provenance. Nothing here is written by hand; the row is the page.

Generated into public/entities/ — gitignored, rebuilt on every deploy, served by server.js
from disk at boot — because 2,800 files that change whenever a sentence in Notion does have
no business in the repository. They share one stylesheet and one script from /assets/
rather than inlining the chrome the way the twenty shelves do: at this count, inlining
would be sixty megabytes.
"""
import html as H
import re
from collections import defaultdict
from pathlib import Path

import chrome

# table key -> route, title field, kind (as the search index names it), anchor prefix, the shelf's built file
KINDS = [
    ("equations", "/equations", "Name", "equation", "", "equations.html"),
    ("theories", "/theories", "Name", "theory", "", "theories.html"),
    ("researchers", "/people", "Name", "researcher", "", "people.html"),
    ("cosmicTimeline", "/timeline", "Event", "event", "", "timeline.html"),
    ("mines", "/mines", "Name", "mine", "", "mines.html"),
    ("machines", "/machines", "Name", "machine", "", "machines.html"),
    ("skills", "/skills", "Name", "skill", "", "skills.html"),
    ("glossary", "/glossary", "Term", "term", "", "glossary.html"),
    ("explainers", "/explainers", "Name", "explainer", "", "explainers.html"),
    ("life", "/life", "Name", "life", "", "life.html"),
    ("impacts", "/impacts", "Name", "impact", "", "impacts.html"),
    ("cosmicStructures", "/scales", "Name", "structure", "", "scales.html"),
    ("observatories", "/cosmos", "Name", "observatory", "obs-", "cosmos.html"),
    ("discoveries", "/cosmos", "Name", "discovery", "disc-", "cosmos.html"),
    ("missions", "/cosmos", "Name", "mission", "mission-", "cosmos.html"),
    ("instruments", "/cosmos", "Name", "instrument", "instr-", "cosmos.html"),
    ("constants", "/constants", "Name", "constant", "", "constants.html"),
    ("forces", "/forces", "Force Name", "force", "", "forces.html"),
]
SKIP_FIELDS = {"id", "url", "lastEdited", "pageId", "pageUrl"}
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# the pages' CSS beyond shared.css and the chrome: small on purpose
CSS = """
  .ent { max-width: 860px; }
  .ent .kcrumb { font: 10.5px ui-monospace, "SF Mono", "Cascadia Code", Consolas, Menlo, monospace; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin: 0 0 8px; }
  .ent .kcrumb a { color: var(--ink-2); text-decoration: none; }
  .ent .facts { display: grid; grid-template-columns: max-content 1fr; gap: 6px 18px; margin: 0 0 22px; font-size: 13px; }
  .ent .facts dt { color: var(--muted); font: 10.5px ui-monospace, "SF Mono", "Cascadia Code", Consolas, Menlo, monospace; letter-spacing: 0.08em; text-transform: uppercase; padding-top: 2px; }
  .ent .facts dd { margin: 0; color: var(--ink); font-variant-numeric: tabular-nums; }
  .ent .prose p { font-size: 14px; line-height: 1.6; color: var(--ink-2); max-width: 66ch; margin: 0 0 10px; }
  .ent .chips { display: flex; flex-wrap: wrap; gap: 5px; margin: 0 0 6px; }
  .ent .chips a.kchip { text-decoration: none; }
  .ent .chips a.kchip:hover { color: var(--ink); border-color: var(--ink-2); }
  .ent .refs .lbl { font: 10px ui-monospace, "SF Mono", "Cascadia Code", Consolas, Menlo, monospace; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin: 8px 0 4px; }
  .ent .kback { margin: 26px 0 0; font-size: 13px; }
  .ent .kback a { color: var(--ink); }
  @media (max-width: 560px) { .ent .facts { grid-template-columns: 1fr; gap: 2px 0; } .ent .facts dd { margin-bottom: 8px; } }
"""


def esc(s) -> str:
    return H.escape(str(s), quote=True)


def humanize(key: str) -> str:
    """camelCase and snake keys as labels; Notion property names are labels already."""
    if " " in key or key[:1].isupper():
        return key
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key).replace("_", " ").lower()


class Catalogue:
    """Every entity the site gives a page, and the id -> link map that resolves relations."""

    def __init__(self, notion, elements, slugify, obj_name, search_rows):
        self.slugify = slugify
        self.entities = []          # dicts: table, kind, route, page_file, name, anchor, path, row
        self.by_id = {}             # notion page id -> {name, href, kind}
        self.reverse = defaultdict(list)   # id -> [(kind, field, name, href)]
        lead = {href: (sub, text) for _, _, sub, text, href in search_rows}
        for table, route, title, kind, prefix, page_file in KINDS:
            for r in notion.get(table, []):
                name = r.get(title)
                if not name:
                    continue
                if table == "constants":
                    sym = r.get("Symbol") or ""
                    anchor = slugify(f"{sym}-{name}" if sym and sym != "—" else name)
                else:
                    anchor = prefix + slugify(name)
                self._add(table, kind, route, page_file, name, anchor, anchor, r, title, lead.get(f"{route}#{anchor}"))
        for o in notion.get("celestialObjects", []):
            nm = obj_name(o)
            if nm and o.get("Type") != "Star" and o.get("Distance from Earth") is not None:
                a = "lg-" + slugify(nm)
                self._add("celestialObjects", "galaxy", "/cosmos", "cosmos.html", nm, a, a, o, "Name", lead.get(f"/cosmos#{a}"))
        for e in elements:
            row = {k: v for k, v in e.items()}
            row["id"] = e["pageId"]
            self._add("elements", "element", "/elements", "index.html", e["name"], e["notation"], e["notation"].lower(), row, "name",
                      lead.get(f"/elements#{e['notation']}"))
        # names for the tables that stay on their shelves, so a relation to a mineral is still a name
        for table, rows in notion.items():
            for r in rows:
                if r.get("id") in self.by_id:
                    continue
                name = r.get("Name") or r.get("Term") or r.get("Event") or r.get("Force Name") or r.get("Object ID")
                if not name:
                    continue
                href = f"/minerals#{name.lower()}" if table in ("minerals", "gemstones") else None
                self.by_id[r["id"]] = {"name": name, "href": href, "kind": table}
        # what points at what
        for e in self.entities:
            for field, val in e["row"].items():
                if field in SKIP_FIELDS or not isinstance(val, list):
                    continue
                for v in val:
                    if isinstance(v, str) and v in self.by_id and v != e["row"].get("id"):
                        self.reverse[v].append((e["kind"], field, e["name"], e["path"]))

    def _add(self, table, kind, route, page_file, name, anchor, slug, row, title_field, lead):
        path = f"{route}/{slug}"
        e = {"table": table, "kind": kind, "route": route, "page_file": page_file, "name": name, "anchor": anchor,
             "path": path, "row": row, "title_field": title_field, "lead": lead}
        self.entities.append(e)
        self.by_id[row["id"]] = {"name": name, "href": path, "kind": kind}

    # ---------------------------------------------------------------- one page
    def render(self, e) -> str:
        row, name = e["row"], e["name"]
        sub, text = e["lead"] or ("", "")
        section = chrome.LABELS.get(e["route"], e["route"].strip("/").title())
        short, prose, rels, lists = [], [], [], []
        for field, val in row.items():
            if field in SKIP_FIELDS or field == e["title_field"] or val in (None, "", []):
                continue
            label = humanize(field)
            if isinstance(val, list):
                ids = [v for v in val if isinstance(v, str) and UUID.match(v)]
                if ids and len(ids) == len(val):
                    items = [self.by_id.get(i) for i in ids]
                    rels.append((label, [x for x in items if x]))
                else:
                    lists.append((label, [str(v) for v in val]))
            elif isinstance(val, str) and (len(val) > 140 or "\n" in val):
                prose.append((label, val))
            elif isinstance(val, bool):
                short.append((label, "yes" if val else "no"))
            else:
                short.append((label, val))

        out = [f"<title>{esc(name)} · Kosmos</title>", "<style>", "</style>", '<article class="ent">',
               f'<p class="kcrumb"><a href="{e["route"]}#{esc(e["anchor"])}">{section}</a> · {esc(e["kind"])}</p>',
               f'<h1 class="ktitle">{esc(name)}</h1>']
        if sub:
            out.append(f'<p class="klede">{esc(sub)}</p>')
        if short:
            out.append('<dl class="facts">' + "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in short) + "</dl>")
        for label, val in prose:
            paras = "".join(f"<p>{esc(p.strip())}</p>" for p in val.split("\n") if p.strip())
            out.append(f'<section class="prose"><h2 class="ksec">{esc(label)}</h2>{paras}</section>')
        for label, vals in lists:
            out.append(f'<section><h2 class="ksec">{esc(label)}</h2><div class="chips">'
                       + "".join(f'<span class="kchip">{esc(v)}</span>' for v in vals) + "</div></section>")
        for label, items in rels:
            if not items:
                continue
            out.append(f'<section><h2 class="ksec">{esc(label)}</h2><div class="chips">'
                       + "".join(self._chip(x) for x in items) + "</div></section>")
        refs = self.reverse.get(row.get("id"), [])
        if refs:
            by_kind = defaultdict(list)
            for kind, field, nm, href in refs:
                by_kind[kind].append((nm, href))
            out.append('<section class="refs"><h2 class="ksec">Referenced by</h2>')
            for kind in sorted(by_kind):
                seen, chips = set(), []
                for nm, href in sorted(by_kind[kind]):
                    if nm in seen:
                        continue
                    seen.add(nm); chips.append(self._chip({"name": nm, "href": href}))
                out.append(f'<div class="lbl">{esc(kind)}</div><div class="chips">{"".join(chips)}</div>')
            out.append("</section>")
        out.append(f'<p class="kback"><a href="{e["route"]}#{esc(e["anchor"])}">Open on the {section} shelf</a> — '
                   "the interactive card, the filters, and everything alongside it.</p>")
        when = (row.get("lastEdited") or "")[:10]
        table = humanize(e["table"]).replace("cosmic timeline", "cosmic timeline").title() if e["table"] != "elements" else "All Periodical Elements"
        out.append(f'<p class="kfoot">From the {esc(table)} database in Notion'
                   + (f", last edited {when}" if when else "") + ". This page is the row, rendered by the build; nothing on it is written by hand.</p>")
        out.append("</article>")
        return "\n".join(out) + "\n"

    @staticmethod
    def _chip(x) -> str:
        if x.get("href"):
            return f'<a class="kchip" href="{esc(x["href"])}">{esc(x["name"])}</a>'
        return f'<span class="kchip">{esc(x["name"])}</span>'

    # ---------------------------------------------------------------- all pages
    def write_all(self, pub: Path, assets: dict, tr, apply_fr) -> list:
        """EN under public/entities/<route>/<slug>.html, FR under public/entities/fr/...
        Returns the entity paths, for the sitemap."""
        root = pub / "entities"
        for old in root.glob("**/*.html"):
            old.unlink()
        paths = []
        for e in self.entities:
            sub, text = e["lead"] or ("", "")
            desc = esc(text or sub) or None   # into a content="…" attribute
            en = chrome.inject(self.render(e), e["page_file"], external=assets, path=e["path"], description=desc)
            f = root / e["path"].lstrip("/")
            f = f.with_suffix(".html")
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(en)
            fr = root / "fr" / e["path"].lstrip("/")
            fr = fr.with_suffix(".html")
            fr.parent.mkdir(parents=True, exist_ok=True)
            fr.write_text(apply_fr(en, e["page_file"], tr))
            paths.append(e["path"])
        return paths
