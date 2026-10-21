# Vérifier une distribution

[English version](DISTRIBUTION.md)

Construire l’archive source et le wheel, puis vérifier leurs métadonnées :

```bash
python -m pip install build twine
python -m build
python -m twine check --strict dist/*
```

Installer l’unique wheel de `dist/` dans un environnement virtuel neuf. Depuis cet environnement, exécuter :

```bash
python tools/check_distribution.py
```

Le contrôle lance `component-manifest-lint --help` et le point d’entrée module depuis un dossier temporaire. Il retire `PYTHONPATH` ; le module utilise le mode isolé de Python. Les sources du checkout ne peuvent pas satisfaire ces imports. La fixture valide incluse exerce aussi les ressources du paquet.

Le workflow de distribution répète ce contrôle sur Ubuntu et Windows avec Python 3.12. Le workflow de tests existant conserve la matrice des versions Python prises en charge. Ce job ne publie pas sur PyPI et ne crée pas de release.

Avant publication, vérifier le nom et la propriété du paquet, relire les fichiers inclus et la licence, choisir un commit testé et une version, puis configurer le mode de publication retenu. Les outils de build nécessitent le réseau ; cela ne change pas le comportement réseau à l’exécution.

Références : [circuit de packaging Python](https://packaging.python.org/en/latest/flow/), [contrôles des distributions](https://packaging.python.org/en/latest/discussions/setup-py-deprecated/).

---

<div align="center">
  <img src="https://raw.githubusercontent.com/jihedbfr-art/jihedbfr-art/main/assets/brand/jihedailabs-logo.svg" alt="JihedAiLabs" width="120"/>
  <br/>
  <sub>Un projet <a href="https://github.com/jihedbfr-art"><b>JihedAiLabs</b></a></sub>
</div>
