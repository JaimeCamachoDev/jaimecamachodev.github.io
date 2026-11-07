#!/usr/bin/env python3
"""Genera index.md (español) y en/index.md (inglés) a partir de _data/categorias.yml,
_data/descripciones_en.yml, la API de GitHub y el registro de npm.

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
        t = re.search(r'(?m)^-?\s*titulo:\s*"([^"]+)"', block)
        d = re.search(r'(?m)^\s*descripcion:\s*"([^"]+)"', block)
        te = re.search(r'titulo_en:\s*"([^"]+)"', block)
        de = re.search(r'descripcion_en:\s*"([^"]+)"', block)
        r = re.search(r"repos:\s*\[(.*?)\]", block, re.S)
        if t and r:
            cats.append({"titulo": t.group(1), "descripcion": d.group(1) if d else "",
                         "titulo_en": te.group(1) if te else t.group(1),
                         "descripcion_en": de.group(1) if de else (d.group(1) if d else ""),
                         "repos": [x.strip() for x in r.group(1).split(",") if x.strip()]})
    return cats


def load_english():
    """Descripciones en inglés: líneas «nombre: "texto"» de _data/descripciones_en.yml."""
    path = os.path.join(ROOT, "_data/descripciones_en.yml")
    if not os.path.exists(path):
        return {}
    text = open(path, encoding="utf-8").read()
    return {m.group(1): m.group(2) for m in re.finditer(r'(?m)^([\w.\-]+):\s*"(.*)"\s*$', text)}


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


# Topics de tecnología que salen como botones de filtro (topic -> etiqueta)
FILTROS = [("vfx-graph", "VFX Graph"), ("shader-graph", "Shader Graph"), ("hlsl", "HLSL"),
           ("amplify-shader-editor", "Amplify"), ("particle-system", "Partículas"), ("vr", "VR"),
           ("render-graph", "RenderGraph"), ("timeline", "Timeline"), ("npm-package", "Paquete npm")]
FILTROS_EN = {"particle-system": "Particles", "npm-package": "npm package"}

# Textos de cada versión de la página
TEXTOS = {
    "es": {"fichero": "index.md", "permalink": "/",
           "intro": "Technical Artist y desarrollador de Unity: efectos visuales, shaders y herramientas de editor para proyectos en tiempo real y VR.",
           "sin_preview": "Sin preview", "npm": "Paquetes npm",
           "npm_desc": "Se instalan desde el Package Manager de Unity añadiendo el registro de npm con el ámbito <code>com.jaimecamachodev</code>.",
           "cols": ("Paquete", "Versión", "Descripción"),
           "buscar": "Buscar efectos, shaders, herramientas…", "buscar_aria": "Buscar en el portfolio",
           "chips_aria": "Filtrar por tecnología", "vacio": "No hay nada que coincida con el filtro."},
    "en": {"fichero": "en/index.md", "permalink": "/en/",
           "intro": "Technical Artist and Unity developer: visual effects, shaders and editor tools for real-time and VR projects.",
           "sin_preview": "No preview", "npm": "npm packages",
           "npm_desc": "Install them from Unity's Package Manager by adding the npm registry with the <code>com.jaimecamachodev</code> scope.",
           "cols": ("Package", "Version", "Description"),
           "buscar": "Search effects, shaders, tools…", "buscar_aria": "Search the portfolio",
           "chips_aria": "Filter by technology", "vacio": "Nothing matches the filter."},
}


def card(repo, info, readme, t, descripcion):
    img = first_image(readme, repo, info.get("default_branch", "main"))
    desc = html.escape(descripcion)
    url = info["html_url"]
    topics = info.get("topics") or []
    tags = html.escape(" ".join(topics))
    texto = html.escape(" ".join([repo, descripcion, *topics]))
    thumb = f'<img src="{html.escape(img)}" alt="{html.escape(repo)}" loading="lazy">' if img else f'<div class="sin-imagen">{t["sin_preview"]}</div>'
    return (f'<a class="tarjeta" href="{url}" data-tags="{tags}" data-texto="{texto}">{thumb}<div class="texto"><strong>{html.escape(repo)}</strong>'
            f'<span>{desc}</span></div></a>'), set(topics)


def npm_packages():
    data = get(f"https://registry.npmjs.org/-/v1/search?text=maintainer:{NPM_USER}&size=50") or {}
    pkgs = []
    for o in data.get("objects", []):
        p = o["package"]
        if not p.get("deprecated") and p["name"].startswith("com.jaimecamachodev."):
            pkgs.append(p)
    return sorted(pkgs, key=lambda p: p["name"])


def collect():
    """Repos públicos por categoría (con su README) y paquetes npm."""
    cats = []
    for cat in load_categories():
        repos = []
        for repo in cat["repos"]:
            info = get(f"https://api.github.com/repos/{USER}/{repo}")
            if not info or info.get("private") or info.get("archived") or info.get("fork") or info.get("disabled"):
                continue
            repos.append((repo, info, get(f"https://api.github.com/repos/{USER}/{repo}/readme", raw=True)))
        cats.append((cat, repos))
    return cats, npm_packages()


def build(lang, cats, pkgs, english):
    t = TEXTOS[lang]
    en = lang == "en"
    out = ["---", "layout: page", "title: Portfolio", f"permalink: {t['permalink']}", f"lang: {lang}", "---", "",
           t["intro"], "", '<div class="portfolio">']
    shown = 0
    secciones, usados = [], set()
    for cat, repos in cats:
        cards = []
        for repo, info, readme in repos:
            desc = info.get("description") or ""
            if en:
                desc = english.get(repo, desc)
            c, topics = card(repo, info, readme, t, desc)
            cards.append(c)
            usados |= topics
        if cards:
            shown += len(cards)
            titulo = cat["titulo_en"] if en else cat["titulo"]
            descripcion = cat["descripcion_en"] if en else cat["descripcion"]
            secciones += ['<section class="categoria">', f'<h2>{html.escape(titulo)}</h2>',
                          f'<p class="cat-desc">{html.escape(descripcion)}</p>',
                          '<div class="rejilla">', *cards, "</div>", "</section>"]
    if pkgs:
        secciones += ['<section class="categoria">', f"<h2>{t['npm']}</h2>",
                      f'<p class="cat-desc">{t["npm_desc"]}</p>',
                      '<table class="paquetes"><tr>' + "".join(f"<th>{c}</th>" for c in t["cols"]) + "</tr>"]
        for p in pkgs:
            desc = p.get("description") or ""
            if en:
                desc = english.get(p["name"], desc)
            texto = html.escape(f'{p["name"]} {desc}')
            secciones.append(f'<tr data-tags="npm-package unity-editor" data-texto="{texto}"><td><a href="https://www.npmjs.com/package/{p["name"]}">{p["name"]}</a></td>'
                             f'<td>{p["version"]}</td><td>{html.escape(desc)}</td></tr>')
        secciones += ["</table>", "</section>"]
        usados.add("npm-package")
    chips = [f'<button type="button" class="filtro-chip" data-tag="{tag}" aria-pressed="false">{html.escape(FILTROS_EN.get(tag, nombre) if en else nombre)}</button>'
             for tag, nombre in FILTROS if tag in usados]
    out += ['<div class="filtro">',
            f'<input type="search" id="filtro-texto" placeholder="{t["buscar"]}" aria-label="{t["buscar_aria"]}" autocomplete="off">',
            f'<div class="filtro-chips" role="group" aria-label="{t["chips_aria"]}">{"".join(chips)}</div>',
            "</div>",
            f'<p id="filtro-vacio" class="cat-desc" hidden>{t["vacio"]}</p>',
            *secciones, "</div>", ""]
    path = os.path.join(ROOT, t["fichero"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write("\n".join(out))
    return shown


def main():
    cats, pkgs = collect()
    english = load_english()
    for lang in TEXTOS:
        shown = build(lang, cats, pkgs, english)
        print(f"{TEXTOS[lang]['fichero']} generado: {shown} repos públicos, {len(pkgs)} paquetes npm")


if __name__ == "__main__":
    sys.exit(main())
