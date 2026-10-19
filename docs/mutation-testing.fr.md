# Contrôles par mutations

[English version](mutation-testing.md)

Lancer depuis la racine du dépôt :

```bash
python -m unittest discover -s tests
python -m unittest discover -s tests -p test_mutations.py
python -m unittest discover -s tests -p test_mapping_keys.py
```

Le test utilise seulement la bibliothèque standard et appelle le vrai `cli.main` sur un fichier temporaire. L'application conserve sa dépendance existante à PyYAML. Les deux fixtures YAML fournissent 3 000 entrées avec la graine `20261019` : suppression d'une clé, remplacement d'une valeur par null/nombre/liste/dictionnaire/chaîne, duplication d'un élément de liste, vidage d'un objet ou troncature du texte. Les types et formats alternent indépendamment ; les sorties texte, JSON, Markdown et SARIF ainsi que les deux langues sont exercées. Les entrées malformées sont transmises à la commande, pas écartées.

Chaque appel doit renvoyer 0, 1 ou 2 sans exception non gérée. Le code 2 doit être accompagné d'un message non vide sur stderr. Aucun des deux flux ne doit contenir `Traceback`. Le test affiche le nombre d'opérations, les codes de sortie et la durée, et échoue au-delà de 120 secondes (garde-fou contre les blocages). La graine fixe répète les mêmes mutations pour les mêmes fixtures et le même interpréteur ; elle ne couvre pas toutes les entrées possibles.

## Défaut reproduit avant correction

Le contrôle des clés dupliquées insérait les clés YAML dans un ensemble Python avant que le chargeur YAML ne puisse rejeter les clés non hachables. Les listes et dictionnaires provoquaient ainsi un `TypeError`. Sur la version 0.2.0 de départ, 176 des 3 000 mutations ont déclenché cet unique défaut. Les deux fichiers minimaux indépendants suivants provoquaient également un traceback :

```yaml
{[]: 0}
```

```yaml
{ {}: 0 }
```

Pour rejouer chaque variante depuis les sources :

```bash
python -c "from pathlib import Path; Path('list-key.yaml').write_text('{[]: 0}', encoding='utf-8'); Path('dict-key.yaml').write_text('{ {}: 0 }', encoding='utf-8')"
PYTHONPATH=src python -m component_manifest_lint list-key.yaml
PYTHONPATH=src python -m component_manifest_lint dict-key.yaml
```

Les deux commandes renvoient désormais 2, avec un diagnostic `invalid YAML` et sans traceback. Deux tests en processus séparés couvrent chacune des variantes dans les quatre formats de sortie. La correction transforme uniquement l'échec d'insertion de la clé en erreur de construction YAML ; elle n'intercepte pas toutes les exceptions à l'entrée de la commande.

## Périmètre mesuré

Sous Windows avec Python 3.12.0, la campagne inchangée de 3 000 cas est passée en 18,993 secondes le 19 octobre 2026 : 1 115 codes 0, 1 648 codes 1 et 237 codes 2. Suppression/null/nombre ont chacun été exécutés 334 fois ; les six autres opérations, 333 fois chacune. La charge de la machine peut modifier la durée. La campagne couvre des mutations YAML issues des fixtures, pas un fuzzing exhaustif, l'épuisement mémoire, les encodages arbitraires ni toutes les fonctions YAML possibles. Ce dépôt ne contient aucune fixture JSON.

La CLI réutilise sa définition de parseur et résout chaque URI une fois par rapport. Le chargeur sûr accéléré CSafeLoader est utilisé si disponible, avec repli sur SafeLoader ; dates conservées comme texte, fusions YAML, refus des doublons et des balises objet non sûres sont testés sur les deux chemins. La mesure complète utilise CSafeLoader ; le budget de durée du repli pur Python n’a pas été validé. Le test garde ouvert le fichier temporaire en écriture et vide le tampon avant chaque lecture réelle de la CLI. Aucune mutation ni assertion supprimée.

Source consultée le 19 octobre 2026 : [documentation PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation), sur les chargeurs et constructeurs sûrs.
