# jaimecamachodev.github.io

Web personal y portfolio: https://jaimecamachodev.github.io

- `index.md` (portada) se **genera automáticamente** con `scripts/generar_portfolio.py`: lee cada repo de `_data/categorias.yml` (descripción y primera imagen del README) y los paquetes `com.jaimecamachodev.*` de npm. Solo aparecen los repos públicos.
- El workflow **Actualizar portfolio** lo regenera cada día, al cambiar `_data/categorias.yml` y a mano desde Actions → *Run workflow*.
- Para añadir un repo nuevo: ponlo en su categoría en `_data/categorias.yml`.
- `_pages/`: páginas fijas (Sobre mí).
