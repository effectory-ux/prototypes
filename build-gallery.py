#!/usr/bin/env python3
"""Bouw de prototype-galerij uit data/ naar dist/index.html.

De lijst staat niet in één bestand maar in data/prototypes/, één JSON per
prototype. Zo raken twee mensen die tegelijk iets toevoegen elkaar nooit.
Dit script leest die bestanden, haalt via de GitHub API op welke pagina's er
in elke bronrepo staan, en rendert template.html.

    ./build-gallery.py                          bouwt dist/
    ./build-gallery.py --check --base origin/main   controleert, schrijft niets

Beide vormen hebben de `gh` CLI nodig, ingelogd (lokaal) of met GH_TOKEN (CI).

De controle is wat de GitHub Action op elke pull request draait. Die blokkeert
op alles wat mis is in de bestanden zelf, en op een pagina die jij toevoegt maar
die niet bestaat. Een verwijzing die al kapot was omdat iemand een bestand in
zijn eigen repo verplaatste, wordt gemeld maar houdt je niet tegen.

Het echte bouwen blokkeert nooit op een dode verwijzing: dan zou het opruimen in
een bronrepo de hele galerij offline halen.
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
DIST = os.path.join(ROOT, "dist")
ASSETS = ("tokens.css", "foundation.css", ".nojekyll")

# Velden die een prototype-bestand mag hebben. Een typo in een veldnaam is
# anders onzichtbaar: het veld wordt gewoon genegeerd en je wijziging doet niets.
REQUIRED = {"name", "desc", "owner", "group", "repo", "path"}
OPTIONAL = {"also", "variants", "autoVariants"}

# Twee soorten problemen, en dat verschil is belangrijk.
#
# "structuur" is iets fout in het bestand zelf: ontbrekend veld, typo in een
# groepsnaam, kapotte JSON. Dat blokkeert altijd, want dat kun jij repareren.
#
# "verwijzing" is een pagina die niet (meer) in de bronrepo staat. Dat kan
# gebeuren zonder dat iemand deze repo aanraakt: verplaatst iemand een bestand
# in zijn eigen repo, dan gaat het hier rammelen. Je kunt zo'n verwijzing niet
# nieuw toevoegen, maar je bent ook niet verantwoordelijk voor een die al kapot
# was. Anders staat jouw wijziging stil door het opruimwerk van een ander, en
# dan leert iedereen de check te negeren.
errors = []
warnings = []
base_refs = None   # verwijzingen die main al had; None = alles is van jou
soft_refs = False  # bij het echte bouwen blokkeert een dode verwijzing nooit


def fail(where, msg, kind="structuur", ref=None):
    if kind == "verwijzing":
        if soft_refs:
            warnings.append(f"{where}: {msg}")
            return
        if base_refs is not None and ref in base_refs:
            warnings.append(f"{where}: {msg} · stond al zo op main")
            return
    errors.append(f"{where}: {msg}")


def warn(msg):
    warnings.append(msg)


def gh(path):
    out = subprocess.run(
        ["gh", "api", path], capture_output=True, text=True, check=False
    )
    if out.returncode != 0:
        detail = (out.stderr or "").strip().splitlines()
        fail("GitHub API", f"{path} mislukt · {detail[0] if detail else 'onbekende fout'}")
        return None
    return json.loads(out.stdout)


def load_json(path):
    """Eén JSON inlezen, met een leesbare fout als de syntax niet klopt."""
    rel = os.path.relpath(path, ROOT)
    try:
        with open(path) as f:
            return rel, json.load(f)
    except json.JSONDecodeError as e:
        fail(rel, f"geen geldige JSON · regel {e.lineno}, {e.msg}")
        return rel, None


def load_data():
    rel, site = load_json(os.path.join(DATA, "site.json"))
    if site is None:
        sys.exit(report())

    repos = {}
    for path in sorted(glob.glob(os.path.join(DATA, "repos", "*.json"))):
        rel, rc = load_json(path)
        if rc is None:
            continue
        key = os.path.basename(path)[:-5]
        if "repo" not in rc:
            fail(rel, "`repo` ontbreekt (bijvoorbeeld \"effectory-ux/cyos\")")
            continue
        repos[key] = {**rc, "_file": rel}

    entries = []
    for path in sorted(glob.glob(os.path.join(DATA, "prototypes", "*.json"))):
        rel, e = load_json(path)
        if e is None:
            continue
        entries.append({**e, "_file": rel, "_slug": os.path.basename(path)[:-5]})

    return site, repos, entries


def check_shape(site, repos, entries):
    """Alles wat we zonder netwerk al kunnen zien: ontbrekende velden, typo's
    in een groepsnaam, een verwijzing naar een repo die niet bestaat."""
    groups = site.get("groups")
    if not groups:
        fail("data/site.json", "`groups` ontbreekt · de galerij heeft die lijst nodig voor de volgorde")
        groups = []

    if not entries:
        fail("data/prototypes/", "geen enkel prototype gevonden")

    for e in entries:
        where = e["_file"]
        missing = REQUIRED - e.keys()
        if missing:
            fail(where, "ontbrekende velden: " + ", ".join(sorted(missing)))
        unknown = e.keys() - REQUIRED - OPTIONAL - {"_file", "_slug"}
        if unknown:
            fail(where, "onbekende velden: " + ", ".join(sorted(unknown)))
        if e.get("group") and e["group"] not in groups:
            fail(
                where,
                f'groep "{e["group"]}" staat niet in data/site.json · '
                f"kies er een uit {', '.join(groups)} of voeg de nieuwe daar toe",
            )
        if e.get("repo") and e["repo"] not in repos:
            fail(
                where,
                f'repo "{e["repo"]}" bestaat niet · '
                f"beschikbaar: {', '.join(sorted(repos))}",
            )
        for v in e.get("variants") or []:
            if not isinstance(v, dict) or "label" not in v or "path" not in v:
                fail(where, "elke variant heeft een `label` en een `path` nodig")

    names = {}
    for e in entries:
        names.setdefault(e.get("name", "").strip().lower(), []).append(e["_file"])
    for name, files in names.items():
        if name and len(files) > 1:
            fail(", ".join(files), f'twee prototypes heten "{name}" · geef ze aparte namen')


def crawl(cfg):
    """Elke kandidaat-pagina in een repo, min de genegeerde."""
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


def auto_variants(entry_path, pages):
    """Label elke pagina van een prototype uit de bestandsnaam, entry eerst.

    Het deel dat de namen delen gaat eraf, dus group-linking-bol.html wordt
    "Bol" in plaats van de prototypenaam op elk chipje te herhalen."""

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
    """Repo-pad naar gepubliceerde URL. Sommige repos publiceren een submap als
    site-root (cyos rsynct site/ op de gh-pages root), vandaar de rewrites."""
    if not base:
        return None
    for pattern, repl in rewrites:
        path = re.sub(pattern, repl, path)
    if path == "index.html":
        return base
    if path.endswith("/index.html"):
        return base.rstrip("/") + "/" + path[: -len("index.html")]
    return base.rstrip("/") + "/" + path


def build_items(site, repos, entries):
    claimed = {k: set() for k in repos}
    items = []

    for entry in entries:
        rc = repos.get(entry.get("repo"))
        if rc is None or "paths" not in rc:
            continue
        where, path = entry["_file"], entry["path"]
        # Bestaat de beginpagina niet meer, dan blijft de kaart wel staan, maar
        # zonder thumbnail. Een prototype dat stil uit de galerij verdwijnt omdat
        # iemand een bestand verplaatste is erger dan een kaart die zegt dat er
        # iets te repareren valt.
        missing_page = path not in rc["paths"]
        if missing_page:
            fail(
                where,
                f"`path` bestaat niet in {rc['repo']}: {path} · "
                "staat de pagina al gepusht in die repo?",
                "verwijzing",
                f"{entry['repo']}::{path}",
            )

        pages = {path}
        for pattern in entry.get("also", []):
            try:
                rx = re.compile(pattern)
            except re.error as e:
                fail(where, f'`also` patroon "{pattern}" is geen geldige regex · {e}')
                continue
            pages |= {p for p in rc["paths"] if rx.search(p)}
        claimed[entry["repo"]] |= pages

        # Een prototype kan meerdere ingangen hebben (zelfde flow, andere data of
        # een andere ontwerprichting); elk wordt een eigen link op de kaart.
        # Zonder expliciete labels worden de pagina's uit hun bestandsnaam benoemd.
        spec = entry.get("variants")
        if spec is None and len(pages) > 1 and entry.get("autoVariants", True):
            spec = auto_variants(path, sorted(pages))

        variants = []
        for v in spec or []:
            if not isinstance(v, dict) or "path" not in v:
                continue
            if v["path"] not in rc["paths"]:
                fail(
                    where,
                    f"variant bestaat niet in {rc['repo']}: {v['path']}",
                    "verwijzing",
                    f"{entry['repo']}::{v['path']}",
                )
                continue
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
                # Stable handle back to this entry, zodat een naam die in de
                # pagina gewijzigd wordt bij het juiste prototype terechtkomt.
                "id": entry["repo"] + "::" + path,
                # Het bestand waar dit prototype in staat, plus de inhoud ervan.
                # Publiceren vanaf de pagina schrijft alleen dit ene bestand, dus
                # een naamswijziging kan niets van iemand anders raken.
                "file": entry["_file"],
                "source": {k: v for k, v in entry.items() if not k.startswith("_")},
                "_key": entry["repo"],
                "name": entry["name"],
                "variants": variants,
                "desc": entry.get("desc", ""),
                "owner": entry["owner"],
                "group": entry["group"],
                "path": path,
                "repos": rc.get("repos", [{"org": rc["repo"].split("/")[0], "name": rc["repo"].split("/")[1]}]),
                "live": None if missing_page else live_url(rc.get("pages"), path, rc.get("liveRewrite", [])),
                "code": f"https://github.com/{rc['repo']}/blob/{rc['branch']}/{path}",
                "tree": f"https://github.com/{rc['repo']}",
                "screens": len(pages),
                "pages": sorted(pages),
            }
        )

    leftovers = []
    for k, r in repos.items():
        for p in sorted(set(r.get("paths", [])) - claimed[k]):
            leftovers.append(f"{r['repo']}/{p}")
    if leftovers:
        warn(
            f"{len(leftovers)} pagina's die geen enkele kaart opeist:\n"
            + "\n".join(f"    {p}" for p in leftovers)
        )

    order = {g: i for i, g in enumerate(site["groups"])}
    items.sort(key=lambda i: (order.get(i["group"], 99), not i["live"], i["name"].lower()))

    # De bronnenlijst in de voettekst volgt de galerij: de repo van de eerste
    # kaart vooraan. Repos zonder kaart sluiten de rij, zodat ze wel zichtbaar
    # blijven maar niet bovenaan staan.
    repo_order = list(dict.fromkeys(i.pop("_key") for i in items))
    repo_order += [k for k in repos if k not in repo_order]
    return items, repo_order


def render(site, repos, items, repo_order, write=True):
    """Altijd renderen, ook bij --check: dan weet je dat de pagina het doet.
    Alleen wegschrijven doen we bij een echte bouw."""
    with open(os.path.join(ROOT, "template.html")) as f:
        tpl = f.read()

    html = (
        tpl.replace("/*__DATA__*/", json.dumps(items, ensure_ascii=False, indent=0))
        .replace("/*__DS__*/", json.dumps(site["designSystem"], ensure_ascii=False))
        .replace(
            "/*__REPOS__*/",
            json.dumps(
                [
                    {"repo": repos[k]["repo"], "pages": repos[k].get("pages")}
                    for k in repo_order
                ],
                ensure_ascii=False,
            ),
        )
        .replace("__COUNT__", str(len(items)))
        # Leeg zolang er geen sync-endpoint is: dan blijven naamswijzigingen
        # lokaal en worden ze per prototype gepubliceerd.
        .replace("/*__SYNC__*/", json.dumps(site.get("sync") or {}, ensure_ascii=False))
    )

    for leftover in re.findall(r"/\*__[A-Z]+__\*/|__[A-Z]+__", html):
        fail("template.html", f"placeholder {leftover} is niet ingevuld")

    if not write:
        return

    os.makedirs(DIST, exist_ok=True)
    with open(os.path.join(DIST, "index.html"), "w") as f:
        f.write(html)
    for asset in ASSETS:
        src = os.path.join(ROOT, asset)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(DIST, asset))
        else:
            open(os.path.join(DIST, asset), "a").close()


def report():
    """Alle problemen in één keer, zodat je niet fout-voor-fout hoeft te fixen."""
    sys.stdout.flush()
    summary = []
    if warnings:
        summary.append("⚠ Let op")
        summary += [f"  {w}" for w in warnings]
    if errors:
        summary.append(f"\n✗ {len(errors)} probleem(en) in de data:")
        summary += [f"  {e}" for e in errors]
    text = "\n".join(summary)
    if text:
        print("\n" + text, file=sys.stderr if errors else sys.stdout)

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary and text:
        with open(step_summary, "a") as f:
            f.write("```\n" + text + "\n```\n")

    return 1 if errors else 0


def git(*args):
    out = subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=ROOT, check=False
    )
    return out.stdout if out.returncode == 0 else None


def refs_of(entries):
    """Elke pagina waar een lijst entries naar wijst, als repo::pad."""
    out = set()
    for e in entries:
        if not isinstance(e, dict) or "repo" not in e:
            continue
        for p in [e.get("path")] + [v.get("path") for v in e.get("variants") or []]:
            if p:
                out.add(f"{e['repo']}::{p}")
    return out


def refs_on(ref):
    """Welke paginaverwijzingen main al had, in de oude of de nieuwe indeling.

    Zo weten we of een dode verwijzing nieuw is (jouw fout, dus blokkeren) of er
    al stond (iemand verplaatste een pagina, dus alleen melden)."""
    entries = []

    listing = git("ls-tree", "-r", "--name-only", ref, "--", "data/prototypes")
    for path in (listing or "").splitlines():
        blob = git("show", f"{ref}:{path}")
        if blob:
            try:
                entries.append(json.loads(blob))
            except json.JSONDecodeError:
                pass

    if not entries:  # main staat nog op de oude indeling
        blob = git("show", f"{ref}:prototypes.json")
        if blob:
            try:
                entries = json.loads(blob).get("entries", [])
            except json.JSONDecodeError:
                entries = []

    return refs_of(entries) if entries else None


def main():
    global base_refs, soft_refs
    check_only = "--check" in sys.argv

    # Bij het echte bouwen publiceren we altijd wat er te publiceren valt: een
    # pagina die iemand verplaatst heeft mag de galerij niet offline houden.
    # Alleen de controle op een pull request blokkeert.
    soft_refs = not check_only

    # --base <ref>: een dode verwijzing die main al had is een waarschuwing,
    # een nieuwe blijft een fout.
    if "--base" in sys.argv:
        i = sys.argv.index("--base")
        ref = sys.argv[i + 1] if len(sys.argv) > i + 1 else "origin/main"
        base_refs = refs_on(ref)
        if base_refs is None:
            print(f"! kon {ref} niet lezen · elke dode verwijzing blokkeert", file=sys.stderr)
        else:
            print(f"Vergeleken met {ref} · {len(base_refs)} bestaande verwijzingen")

    site, repos, entries = load_data()
    check_shape(site, repos, entries)

    print("Repos uitlezen")
    for key, rc in repos.items():
        got = crawl(rc)
        if got:
            repos[key] = {**rc, **got}

    items, repo_order = build_items(site, repos, entries)
    render(site, repos, items, repo_order, write=not check_only)

    if errors:
        sys.exit(report())

    print(f"\n{len(items)} prototypes uit {len(repos)} repos")
    report()
    if check_only:
        print(f"\n✓ data is in orde · de pagina rendert met {len(items)} kaarten")
    else:
        print(f"\n✓ dist/index.html geschreven · {len(items)} kaarten")


if __name__ == "__main__":
    main()
