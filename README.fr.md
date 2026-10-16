<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="120" height="120">
</p>

# component-manifest-lint

[English version](README.md)

Vérifie un manifeste de composant télécom (la ressource Kubernetes `Component` du Canvas de l'Open Digital Architecture) avant qu'il n'atteigne un cluster : champs inconnus ou mal orthographiés, champs obligatoires absents, mauvais types, et incohérences entre le manifeste et ses propres services. Hors ligne, une seule dépendance (PyYAML), sans IA.

> Projet indépendant. Sans affiliation, approbation ni certification de TM Forum. Un résultat propre ne dit rien de la conformité ni d'une certification.

## Pourquoi cet outil

Le schéma publié d'un `Component` a peu de champs obligatoires et ne conserve pas les champs inconnus : un `exposedApis` mal écrit n'est donc pas une erreur, il est simplement ignoré par le cluster, et on s'en aperçoit quand le composant n'expose pas ce qu'on avait écrit. L'outil lit le même schéma publié et vous prévient avant le déploiement. Il vérifie aussi ce que le schéma ne peut pas vérifier : que `implementation` désigne un vrai Service et que le port correspond, que les noms d'API sont uniques, que les URL de spécification ne suivent pas une branche mouvante.

## Démarrage rapide

Python 3.10 ou plus et PyYAML :

```bash
git clone https://github.com/jihedbfr-art/component-manifest-lint.git
cd component-manifest-lint
pip install pyyaml
PYTHONPATH=src python -m component_manifest_lint --lang fr fixtures/order-desk.weak.yaml
```

Ou `pip install .` puis `component-manifest-lint FICHIER [FICHIER ...]`. Plusieurs documents par fichier sont acceptés ; seuls les documents `kind: Component` sont contrôlés, et les Services du même fichier servent aux recoupements. Un modèle Helm doit d'abord être rendu (`helm template`) : l'outil refuse les fichiers qui contiennent encore `{{`.

Options : `--lang en|fr`, `--format text|json|md`, `--fail-on error|warn|never` (défaut `error`). Codes de sortie : `0` quand aucun constat n'atteint le niveau `--fail-on`, `1` sinon, `2` pour un fichier illisible ou invalide.

## Ce qui est contrôlé

| Règle | Niveau | Fondée sur | Contrôle |
|---|---|---|---|
| M001 | avert. | schéma publié | un champ que le schéma de cette `apiVersion` ne définit pas |
| M002 | avert. | schéma publié | `apiVersion` n'est pas l'une des versions publiées (`v1`, `v1beta2`, `v1beta3`, `v1beta4`) |
| M006 | erreur | schéma publié | un champ que le schéma déclare obligatoire est absent |
| M012 | erreur | schéma publié | un champ a le mauvais type (par exemple `dependentAPIs` est une chaîne) |
| M003 | info | deux exemples publics | le label `oda.tmforum.org/componentName` est égal à `metadata.name` |
| M004 | info | jugement | `componentMetadata` a id, name, version, description |
| M005 | avert. | jugement | `componentMetadata.version` ressemble à MAJEUR.MINEUR.CORRECTIF |
| M007 | avert. | cohérence | `implementation` désigne un Service du même fichier (seulement si le fichier a des Services) |
| M008 | avert. | cohérence | le `port` de l'API est l'un des ports de ce Service |
| M009 | info | deux exemples publics | le `path` de l'API commence par `/` + le nom du composant |
| M010 | avert. | cohérence | un nom d'API apparaît deux fois dans une même section de fonction |
| M011 | info | jugement | une URL de spécification pointe vers `master`, `main` ou `HEAD` au lieu d'un commit ou d'une étiquette |

Les preuves de chaque règle, et le commit d'où le schéma a été tiré, sont dans [docs/evidence.fr.md](docs/evidence.fr.md).

## Limites

- Contrôles statiques de fichiers. Ni cluster, ni webhook d'admission, ni réseau : un Canvas en marche peut accepter ou rejeter autrement.
- Le fichier de schéma du paquet est un instantané (voir la page de preuves). Régénérez-le avec `tools/extract_schema.py` quand le schéma publié change.
- Les parties libres du schéma (comme la gestion des secrets) ne sont pas contrôlées à l'intérieur.
- Les règles de jugement sont des suggestions ; avec `--fail-on error`, seules les erreurs de schéma font échouer.

## Tests

```bash
python -m unittest discover -s tests
```

18 tests. Les jeux d'essai sont des manifestes inventés dans `fixtures/`.

## Licence et contact

Code : [Apache License 2.0](LICENSE). Des fonctions avancées peuvent être discutées sur demande : voir [COMMERCIAL.fr.md](COMMERCIAL.fr.md).

---

<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="80" height="80"><br>
  <sub>Conçu et maintenu sous <b>JihedAiLabs</b>.</sub>
</p>
