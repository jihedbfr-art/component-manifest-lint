# Preuves derrière les contrôles

[English version](evidence.md)

Lu le 2026-10-16. Rien ici ne copie un manifeste ni un texte de schéma : le dépôt embarque un petit arbre de schéma extrait d'un fichier public, et cite sa provenance.

## Le schéma

`src/component_manifest_lint/schema.json` a été généré par `tools/extract_schema.py` à partir de la définition de ressource `Component` du dépôt public du Canvas, figée au commit `c39da6340dbc` :
[oda-component-crd.yaml](https://github.com/tmforum-oda/oda-canvas/blob/c39da6340dbc/charts/oda-crds/templates/oda-component-crd.yaml). Le dépôt déclare Apache-2.0.

Ce que dit ce fichier, et les règles qui en découlent :

- Quatre versions sont servies : `v1beta2`, `v1beta3`, `v1beta4` et `v1` (M002). Seule `v1` est marquée comme version de stockage.
- Les champs obligatoires sont peu nombreux : `name` et `specification` pour les API core et security, `name` pour les API de management, `type` et `podSelector` pour la gestion des secrets (M006). L'essentiel du manifeste est facultatif.
- Seuls deux nœuds conservent les champs inconnus (`secretsManagement` et `status`). Partout ailleurs le schéma est fermé, d'où M001 : ces champs ne font pas partie de la ressource publiée.
- Les types des champs sont déclarés (M012).

L'affirmation qu'un cluster « ignorera très probablement » un champ inconnu découle du traitement par Kubernetes des schémas structurels sans l'option de conservation des champs inconnus ; elle n'a pas été testée sur un cluster en marche ici.

## Les exemples publics

Les règles M003 et M009 viennent de deux manifestes du dépôt public d'exemples, figé au commit `be11fd016144` : le [manifeste source Product Inventory](https://github.com/tmforum-oda/reference-example-components/blob/be11fd016144/source/ProductInventory/test-instance.component.yaml) et le modèle de chart Party Management. Dans les deux, le label `oda.tmforum.org/componentName` est égal au nom du composant et chaque chemin d'API exposée commence par `/` suivi de ce nom. Deux exemples sont une preuve mince, d'où le niveau `info` de ces règles. Le dépôt déclare Apache-2.0.

Six autres modèles de chart de ce dépôt n'ont pas pu être lus par le dé-modelage rapide utilisé ici ; ils n'ont donc pas servi de preuve.

## Passage sur un vrai manifeste

Le manifeste source Product Inventory ci-dessus donne deux constats `info` et rien d'autre : deux URL de spécification pointent vers la branche `master` (M011). Il n'a ni avertissement ni erreur.

## Ce que cela n'établit pas

Rien ici ne montre une conformité, une certification ni l'acceptation par un Canvas en marche. M004, M005 et M011 sont des jugements, pas des exigences.
