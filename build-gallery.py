#!/usr/bin/env python3
"""Regenerate index.html for the Effectory UX prototype gallery.

One card per prototype, not per page. prototypes.json lists the entry page of
each prototype; `also` patterns claim the rest of its screens so the card can
show a screen count. Any page that no entry claims is reported as a leftover,
so new prototypes do not silently go missing from the gallery.

Usage:  ./build-gallery.py        (needs the `gh` CLI, authenticated)
"""

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))


def gh(path):
    out = subprocess.run(
        ["gh", "api", path], capture_output=True, text=True, check=False
    )
    if out.returncode != 0:
        print(f"  ! api mislukt: {path}", file=sys.stderr)
        return None
    return json.loads(out.stdout)


def crawl(key, cfg):
    """Every candidate prototype page in a repo, minus the ignored ones."""
    meta = gh(f"repos/{cfg['repo']}")
    if meta is None:
        return None
    branch = meta["default_branch"]
    tree = gh(f"repos/{cfg['repo']}/git/trees/{branch}?recursive=1")
    if tree is None:
        return None
    ignore = [re.compile(p) for p in cfg.get("ignore", [])]
    paths = [
        n["path"]
        for n in tree["tree"]
        if n["type"] == "blob"
        and n["path"].endswith(".html")
        and not any(p.search(n["path"]) for p in ignore)
    ]
    print(f"  {cfg['repo']} · branch {branch} · {len(paths)} pagina's")
    return {"branch": branch, "paths": paths}


def last_commit(repo, path):
    """Date of the newest commit touching this path, empty string if unknown."""
    out = subprocess.run(
        ["gh", "api", f"repos/{repo}/commits?path={path}&per_page=1",
         "--jq", ".[0].commit.committer.date"],
        capture_output=True, text=True, check=False,
    )
    return out.stdout.strip()


def stem(path):
    """Filename without extension; a folder index is named after its folder."""
    last = path.rsplit("/", 1)[-1]
    return path.split("/")[-2] if last == "index.html" and "/" in path else last[:-5]


def pretty(path, prefix=""):
    # The index page is the way into most prototypes and gets its own row in the
    # dialog, so it is named for what it is rather than for its filename.
    if path == "index.html":
        return "Main page"
    rest = stem(path)[len(prefix):].lstrip("-") if prefix and stem(path).startswith(prefix) else stem(path)
    return rest.replace("-", " ").replace("/", " · ").strip().capitalize() or "Main page"


def auto_variants(entry_path, pages):
    """Label every page of a prototype from its filename, entry page first.

    The part the filenames share is dropped, so group-linking-bol.html becomes
    "Bol" rather than repeating the prototype name on every chip."""
    def stem(p):
        s = p.rsplit("/", 1)[-1]
        return p.split("/")[-2] if s == "index.html" and "/" in p else s[:-5]

    stems = [stem(p) for p in pages]
    prefix = os.path.commonprefix(stems).rstrip("-") if len(stems) > 1 else ""

    out = []
    for p in sorted(pages, key=lambda p: (p != entry_path, p)):
        rest = stem(p)[len(prefix):].lstrip("-") if prefix else stem(p)
        label = rest.replace("-", " ").strip().capitalize() or "Basis"
        out.append({"label": label, "path": p})
    return out


def live_url(base, path, rewrites=()):
    """Repo path to published URL. Some repos publish a subfolder as the site
    root (cyos rsyncs site/ onto the gh-pages root), hence the rewrites."""
    if not base:
        return None
    for pattern, repl in rewrites:
        path = re.sub(pattern, repl, path)
    if path == "index.html":
        return base
    if path.endswith("/index.html"):
        return base.rstrip("/") + "/" + path[: -len("index.html")]
    return base.rstrip("/") + "/" + path


def main():
    with open(os.path.join(ROOT, "prototypes.json")) as f:
        cfg = json.load(f)

    print("Repos uitlezen")
    repos = {}
    for key, rc in cfg["repos"].items():
        got = crawl(key, rc)
        if got is None:
            sys.exit(f"✗ kon {rc['repo']} niet lezen")
        repos[key] = {**rc, **got}

    claimed = {k: set() for k in repos}
    items = []
    hidden = []

    for entry in cfg["entries"]:
        rc = repos[entry["repo"]]
        path = entry["path"]
        if path not in rc["paths"]:
            sys.exit(f"✗ entry-pagina bestaat niet: {rc['repo']}/{path}")

        pages = {path}
        for pattern in entry.get("also", []):
            rx = re.compile(pattern)
            pages |= {p for p in rc["paths"] if rx.search(p)}
        claimed[entry["repo"]] |= pages

        # A prototype can have several entry points (same flow, different data or
        # a different design direction); each becomes its own link on the card.
        # Without explicit labels the pages are labelled from their filenames.
        spec = entry.get("variants")
        if spec is None and len(pages) > 1 and entry.get("autoVariants", True):
            spec = auto_variants(path, sorted(pages))

        variants = []
        for v in spec or []:
            if v["path"] not in rc["paths"]:
                sys.exit(f"✗ variant bestaat niet: {rc['repo']}/{v['path']}")
            pages.add(v["path"])
            claimed[entry["repo"]].add(v["path"])
            variants.append(v)

        # Hidden: keep the entry (name, group, owner, desc) and let it claim its
        # pages so they stay out of the leftovers, but render no card. Skipping
        # here also saves the per-page commit lookups below.
        if entry.get("hidden"):
            hidden.append(entry["name"])
            continue

        # Every page of the prototype becomes a link, not just the curated entry
        # points: the main page first, then the labelled ones in the order they are
        # declared, then the rest by path. Curated labels win; the others are derived
        # from the filename with the shared prefix dropped.
        labels = {v["path"]: v["label"] for v in variants}
        volgorde = {v["path"]: i + 1 for i, v in enumerate(variants)}
        volgorde[path] = 0
        stems = [stem(pg) for pg in pages]
        prefix = os.path.commonprefix(stems).rstrip("-") if len(stems) > 1 else ""

        # A prototype can have a tested winner: the version usability testing picked,
        # and the one to keep building on. It gets a chip on the card and a marker on
        # its page in the dialog, so nobody has to guess which variant is current.
        winner = entry.get("winner")
        if winner and winner["path"] not in pages:
            sys.exit(f"✗ winner-pagina bestaat niet: {rc['repo']}/{winner['path']}")

        links = []
        for pg in sorted(pages, key=lambda pg: (volgorde.get(pg, 999), pg)):
            links.append(
                {
                    "label": labels.get(pg) or pretty(pg, prefix),
                    "live": live_url(rc.get("pages"), pg, rc.get("liveRewrite", [])),
                    "code": f"https://github.com/{rc['repo']}/blob/{rc['branch']}/{pg}",
                    **({"winner": True} if winner and pg == winner["path"] else {}),
                }
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            dates = [d for d in pool.map(lambda pg: last_commit(rc["repo"], pg), sorted(pages)) if d]
        updated = max(dates) if dates else ""

        items.append(
            {
                "updated": updated,
                # Stable handle back to this entry in prototypes.json, so a rename
                # made in the page can be written to the right entry.
                "id": entry["repo"] + "::" + path,
                "name": entry["name"],
                "variants": links,
                "winner": entry.get("winner"),
                "desc": entry.get("desc", ""),
                "owner": entry["owner"],
                "group": entry["group"],
                "path": path,
                "repos": rc["repos"],
                "live": live_url(rc.get("pages"), path, rc.get("liveRewrite", [])),
                "code": f"https://github.com/{rc['repo']}/blob/{rc['branch']}/{path}",
                "tree": f"https://github.com/{rc['repo']}",
                "screens": len(pages),
                "pages": sorted(pages),
            }
        )

    print(f"\n{len(items)} prototypes uit {len(repos)} repos")
    if hidden:
        print(f"{len(hidden)} verborgen (geen kaart): " + ", ".join(sorted(hidden)))

    leftovers = {
        k: sorted(set(r["paths"]) - claimed[k]) for k, r in repos.items()
    }
    total_left = sum(len(v) for v in leftovers.values())
    if total_left:
        print(f"\n⚠ {total_left} pagina's die geen enkele kaart opeist:")
        for k, paths in leftovers.items():
            for p in paths:
                print(f"    {repos[k]['repo']}/{p}")
    else:
        print("\n✓ elke pagina hoort bij een prototype")

    # Newest first. The page groups by track when a track is selected, but the
    # order inside any view is always most recently updated.
    items.sort(key=lambda i: (i["updated"] or "", i["name"].lower()), reverse=True)

    nieuwste = [f"{i['updated'][:10]}  {i['name']}" for i in items[:3]]
    print("\nmeest recent bijgewerkt:")
    for r in nieuwste:
        print("   " + r)

    with open(os.path.join(ROOT, "template.html")) as f:
        tpl = f.read()

    html = (
        tpl.replace("/*__DATA__*/", json.dumps(items, ensure_ascii=False, indent=0))
        .replace("/*__DS__*/", json.dumps(cfg["designSystem"], ensure_ascii=False))
        .replace(
            "/*__REPOS__*/",
            json.dumps(
                [{"repo": r["repo"], "pages": r.get("pages")} for r in repos.values()],
                ensure_ascii=False,
            ),
        )
        .replace("__COUNT__", str(len(items)))
        # The page needs the source config verbatim to be able to write a renamed
        # prototypes.json for the GitHub editor.
        .replace("/*__CONFIG__*/", json.dumps(cfg, ensure_ascii=False))
    )

    with open(os.path.join(ROOT, "index.html"), "w") as f:
        f.write(html)

    print(f"\n✓ index.html geschreven · {len(items)} kaarten")


if __name__ == "__main__":
    main()
