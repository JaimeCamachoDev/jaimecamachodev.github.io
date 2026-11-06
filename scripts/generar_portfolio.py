#!/usr/bin/env python3
"""Genera index.md (portfolio) a partir de _data/categorias.yml, la API de GitHub y el registro de npm.

Uso: GITHUB_TOKEN=... python3 scripts/generar_portfolio.py
"""
import base64, html, json, os, re, sys, urllib.request, urllib.error

USER = "JaimeCamachoDev"
NPM_USER = "jaimecamachodev"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get(url, raw=False):
    headers = {"Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json", "User-Agent": "portfolio"}
    if TOKEN and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {TOKEN}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
            data = r.read().decode("utf-8", "replace")
            return data if raw else json.loads(data)
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return None


def load_categories():
    # YAML mínimo (listas de "- titulo/descripcion/repos: [..]") sin dependencias externas
    text = open(os.path.join(ROOT, "_data/categorias.yml"), encoding="utf-8").read()
    text = re.sub(r"#.*", "", text)
    cats = []
    for block in re.split(r"\n(?=- )", text.strip()):
        t = re.search(r'titulo:\s*"([^"]+)"', block)
        d = re.search(r'descripcion:\s*"([^"]+)"', block)
        r = re.search(r"repos:\s*\[(.*?)\]", block, re.S)
        if t and r:
            cats.append({"titulo": t.group(1), "descripcion": d.group(1) if d else "",
                         "repos": [x.strip() for x in r.group(1).split(",") if x.strip()]})
    return cats


# Banner de relleno de la plantilla (está en un repo privado: no se ve públicamente)
PLACEHOLDERS = ("5b933a56-0ece-452a-99c0-1a641485a6b9",)


def first_image(readme, repo, branch):
    """Primera imagen del README; las rutas relativas (p. ej. .github/preview.gif) se resuelven al repo."""
    if not readme:
        return None
    # Los bloques de código (``` o ~~~) pueden traer ejemplos de imágenes que no existen
    readme = re.sub(r"^(```|~~~).*?^\1", "", readme, flags=re.S | re.M)
    for m in re.finditer(r"!\[[^\]]*\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)|<img[^>]+src=\"([^\"]+)\"", readme):
        url = m.group(1) or m.group(2)
        if any(p in url for p in PLACEHOLDERS):
            continue
        if not re.match(r"https?://", url):
            # github.com/<user>/<repo>/raw/... sirve tanto ficheros normales como de Git LFS
            # (raw.githubusercontent.com devuelve solo el puntero de LFS).
            # Se quita el prefijo "./" o "/", no caracteres sueltos: lstrip("./") rompía ".github/...".
            path = re.sub(r"^(\./|/)+", "", url)
            url = f"https://github.com/{USER}/{repo}/raw/{branch}/{path}"
        return url
    return None


def card(repo, info, readme):
    img = first_image(readme, repo, info.get("default_branch", "main"))
    desc = html.escape(info.get("description") or "")
    url = info["html_url"]
    thumb = f'<img src="{html.escape(img)}" alt="{html.escape(repo)}" loading="lazy">' if img else '<div class="sin-imagen">Sin preview</div>'
    return (f'<a class="tarjeta" href="{url}">{thumb}<div class="texto"><strong>{html.escape(repo)}</strong>'
            f'<span>{desc}</span></div></a>')


def npm_packages():
    data = get(f"https://registry.npmjs.org/-/v1/search?text=maintainer:{NPM_USER}&size=50") or {}
    pkgs = []
    for o in data.get("objects", []):
        p = o["package"]
        if not p.get("deprecated") and p["name"].startswith("com.jaimecamachodev."):
            pkgs.append(p)
    return sorted(pkgs, key=lambda p: p["name"])


def main():
    out = ["---", "layout: page", "title: Portfolio", "permalink: /", "---", "",
           "Technical Artist y desarrollador de Unity: efectos visuales, shaders y herramientas de editor para proyectos en tiempo real y VR.",
           "", '<div class="portfolio">']
    shown = 0
    for cat in load_categories():
        cards = []
        for repo in cat["repos"]:
            info = get(f"https://api.github.com/repos/{USER}/{repo}")
            if not info or info.get("private") or info.get("archived") or info.get("fork") or info.get("disabled"):
                continue
            readme = get(f"https://api.github.com/repos/{USER}/{repo}/readme", raw=True)
            cards.append(card(repo, info, readme))
        if cards:
            shown += len(cards)
            out += [f'<h2>{html.escape(cat["titulo"])}</h2>', f'<p class="cat-desc">{html.escape(cat["descripcion"])}</p>',
                    '<div class="rejilla">', *cards, "</div>"]
    pkgs = npm_packages()
    if pkgs:
        out += ["<h2>Paquetes npm</h2>",
                '<p class="cat-desc">Se instalan desde el Package Manager de Unity añadiendo el registro de npm con el ámbito <code>com.jaimecamachodev</code>.</p>',
                '<table class="paquetes"><tr><th>Paquete</th><th>Versión</th><th>Descripción</th></tr>']
        for p in pkgs:
            out.append(f'<tr><td><a href="https://www.npmjs.com/package/{p["name"]}">{p["name"]}</a></td>'
                       f'<td>{p["version"]}</td><td>{html.escape(p.get("description") or "")}</td></tr>')
        out.append("</table>")
    out += ["</div>", ""]
    open(os.path.join(ROOT, "index.md"), "w", encoding="utf-8").write("\n".join(out))
    print(f"index.md generado: {shown} repos públicos, {len(pkgs)} paquetes npm")


if __name__ == "__main__":
    sys.exit(main())
