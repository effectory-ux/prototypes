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

        # A prototype can have several entry points (same flow, different data);
        # each becomes its own link on the card.
        variants = []
        for v in entry.get("variants", []):
            if v["path"] not in rc["paths"]:
                sys.exit(f"✗ variant bestaat niet: {rc['repo']}/{v['path']}")
            pages.add(v["path"])
            claimed[entry["repo"]].add(v["path"])
            variants.append(
                {
                    "label": v["label"],
                    "live": live_url(rc.get("pages"), v["path"], rc.get("liveRewrite", [])),
                    "code": f"https://github.com/{rc['repo']}/blob/{rc['branch']}/{v['path']}",
                }
            )

        items.append(
            {
                "name": entry["name"],
                "variants": variants,
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

    order = {g: i for i, g in enumerate(dict.fromkeys(e["group"] for e in cfg["entries"]))}
    items.sort(key=lambda i: (order[i["group"]], not i["live"], i["name"].lower()))

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
    )

    with open(os.path.join(ROOT, "index.html"), "w") as f:
        f.write(html)

    print(f"\n✓ index.html geschreven · {len(items)} kaarten")


if __name__ == "__main__":
    main()
