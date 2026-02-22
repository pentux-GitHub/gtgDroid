# gtgDroid — Journal de développement

## Vision

Application Android de gestion de tâches GTD, clone mobile de GTG (Getting Things GNOME), synchronisée via CalDAV avec Nextcloud. Objectif final : publier sur F-Droid.

---

## Architecture du projet

```
gtgDroid/
├── main.py                  # App Kivy + ScreenManager
├── caldav_api.py            # Toute la logique CalDAV (fetch, create, update, delete)
├── state.py                 # Variables globales et cache local
├── widgets.py               # Composants réutilisables (confirm_popup, loading_popup)
├── config.py                # URL, USERNAME, PASSWORD Nextcloud (non versionné)
├── config-sample.py         # Modèle de configuration pour les contributeurs
├── screens/
│   ├── __init__.py
│   ├── loading.py           # Écran de chargement au démarrage
│   ├── tags.py              # Liste des tags avec compteur + boutons de vue
│   ├── tasks.py             # Liste des tâches d'un tag
│   ├── detail.py            # Détail d'une tâche
│   └── new_task.py          # Formulaire création/modification/sous-tâche
├── NotoColorEmoji.ttf
├── NotoEmoji.ttf
├── .gitignore               # Exclut config.py, .venv/, __pycache__/, *.log
├── Suivi/
│   ├── gtgDroid.md          # Ce fichier
│   └── GTGDroid_vision.md
└── .venv/                   # Python 3.13, Kivy 2.3.1, caldav 2.2.6
```

### Lancer l'application

```bash
cd /home/pentux/Documents/IT/gtgDroid
source .venv/bin/activate
python3 main.py
```

### Premier démarrage (contributeur)

```bash
cp config-sample.py config.py
# Éditer config.py avec ses credentials Nextcloud
```

---

## Modèle de données

### Tuple tâche (8 éléments)

```python
(title, status, due_str, start_str, description, task_uid, priority, has_children)
#  [0]    [1]     [2]      [3]         [4]          [5]       [6]       [7]
```

| Index | Champ | Type | Exemple |
|-------|-------|------|---------|
| 0 | title | str | `"Préparer le marché"` |
| 1 | status | str | `"NEEDS-ACTION"`, `"COMPLETED"` |
| 2 | due_str | str | `"31/12/2025"` ou `""` |
| 3 | start_str | str | `"01/12/2025"` ou `""` |
| 4 | description | str | Notes libres |
| 5 | task_uid | str | UUID CalDAV |
| 6 | priority | int | `0`, `5`, `9` |
| 7 | has_children | bool | `True` si la tâche a des sous-tâches |

> ⚠️ Tout code qui dépacke le tuple doit inclure `has_children` en 8e position.

### Variables globales et cache (`state.py`)

```python
PAR_TAG = {}          # dict {tag: [tuple_tâche, ...]} — tâches ouvertes
PAR_TAG_CLOSED = {}   # dict {tag: [tuple_tâche, ...]} — tâches fermées
CURRENT_TAG = ''      # tag sélectionné en cours
CURRENT_VIEW = 'open' # vue active : 'open', 'actionable', 'closed'

# Cache local — chargé une seule fois au démarrage via fetch_all()
TAGS_PAR_UID = {}     # {task_uid: "IT, urgent"} — tous les tags d'une tâche
SUBTASKS_PAR_UID = {} # {task_uid: [tuple_tâche, ...]} — sous-tâches triées A→Z
```

---

## Architecture réseau — principe fondamental

### Un seul fetch au démarrage

`fetch_all()` fait **un seul passage** sur Nextcloud et remplit simultanément les 4 structures de `state.py`. Après ce fetch initial, **zéro appel réseau** n'est nécessaire pour naviguer, afficher des tags, ou afficher des sous-tâches.

```
Démarrage → fetch_all() → state.PAR_TAG
                        → state.PAR_TAG_CLOSED
                        → state.TAGS_PAR_UID
                        → state.SUBTASKS_PAR_UID
```

Les appels réseau ne se font qu'à l'**écriture** : `create_task`, `update_task`, `delete_task`, `mark_as_done`, `reset_and_clone_task`. Après chaque écriture, `fetch_all()` est rappelé pour resynchroniser le cache.

### Performances validées (140 tâches, Nextcloud distant)
- Chargement initial : ~8 secondes (fetch_all unique)
- Navigation entre écrans : instantanée (lecture cache)
- Transitions fluides : zéro blocage réseau pendant les animations

---

## Fonctions `caldav_api.py`

| Fonction | Réseau | Description |
|----------|--------|-------------|
| `get_client()` | oui | Nouvelle instance DAVClient |
| `_clean_tags(tags)` | non | Retire `@`, filtre `DAV_gtg` |
| `_parse_tags(tag_str)` | non | `"IT, @urgent"` → `['IT', 'urgent']` |
| `fetch_all()` | oui | **Fetch principal** — remplit tout state |
| `fetch_tasks()` | oui | Appelle `fetch_all()`, retourne `PAR_TAG` |
| `fetch_tasks_completed()` | non | Retourne `PAR_TAG_CLOSED` depuis cache |
| `fetch_subtasks(parent_uid)` | non | Retourne depuis `SUBTASKS_PAR_UID` |
| `fetch_tags_for_uid(uid)` | non | Retourne depuis `TAGS_PAR_UID` |
| `create_task(title, tags, ...)` | oui | Multi-tags supporté |
| `create_subtask(parent_uid, ...)` | oui | Crée avec RELATED-TO |
| `update_task(uid, title, tags, ...)` | oui | Multi-tags, dates en vDatetime UTC |
| `delete_task(uid)` | oui | Suppression définitive |
| `mark_as_done(uid)` | oui | `todo.complete()` |
| `reset_and_clone_task(uid)` | oui | Archive + recrée avec sous-tâches |

---

## Navigation entre écrans

```
LoadingScreen → TagsScreen → TasksScreen → DetailScreen → NewTaskScreen
                                               ↕ (sous-tâches, retour au parent)
```

- Direction `left` : avancer
- Direction `right` : reculer
- Navigation sous-tâche : `load_task(sub_data, from_parent_data=task_data)` — retour automatique au parent, profondeur illimitée
- Après édition : `detail` rechargé avec les données fraîches du cache

---

## Sous-tâches

### Stockage CalDAV
Champ standard `RELATED-TO` :
```
RELATED-TO;RELTYPE=PARENT:[uid_parent]
```
Compatible GTG desktop, tasks.org, Nextcloud.

### Tri
Alphabétique. Convention recommandée : `01-`, `02-` ou `A-`, `B-` pour contrôler l'ordre.

### Affichage dans le détail
- Cases `○` / `✓` cochables directement
- Bouton `>` pour naviguer dans le détail de chaque enfant
- Bouton `+ Ajouter une sous-tâche` toujours visible
- Retour depuis l'enfant → revient sur le parent

### Indicateurs visuels
- Liste des tâches : icône `▶` et fond bleuté
- Détail : titre préfixé `▶` en bleu
- Liste des tags : indicateur `▶` sur le tag

---

## Affichage des tags

### Dans la liste des tâches (`tasks.py`)
- Tag courant : affiché dans le header `#IT`
- Autres tags : affichés en petit sous le titre de chaque tâche
- Source : `state.TAGS_PAR_UID` — instantané, zéro réseau

### Dans le détail (`detail.py`)
- Tags affichés en jaune doré sous le titre : `@IT  @urgent`
- Source : `state.TAGS_PAR_UID` — instantané, zéro réseau

### Convention GTG
- GTG stocke les tags avec `@` en CalDAV
- `_clean_tags()` retire le `@` à la lecture
- `_parse_tags()` retire le `@` à l'écriture
- `@DAV_gtg` : tag technique GTG, filtré partout, jamais affiché
- Saisie multi-tags : `IT, urgent, perso` (virgule comme séparateur)

---

## Réinitialiser une tâche récurrente

> **Vocabulaire** : "récurrent" ≠ "cyclique". Les marchés et renouvellements médicaments sont récurrents mais non cycliques — RRULE n'est pas adapté.

### Bouton `↺ Réinitialiser → "Un jour"`
1. Archive la tâche et ses sous-tâches (COMPLETED)
2. Recrée une copie fraîche : même titre, mêmes sous-tâches, PRIORITY=9, sans dates

### Différence avec "Marquer comme faite"
| Action | Effet | Sous-tâches |
|--------|-------|-------------|
| ✓ Marquer comme faite | Archive uniquement | Non touchées |
| ↺ Réinitialiser | Archive + recrée | Archivées ET recréées |

---

## Gestion des dates fuzzy

### Solution : champ PRIORITY CalDAV
| Bouton gtgDroid | PRIORITY | GTG desktop |
|-----------------|----------|-------------|
| Maintenant | 0 | Pas de date |
| Bientôt | 5 | Ignoré |
| Un jour | 9 | Ignoré |

### Format des dates dans update_task
Nextcloud (SabreDAV) est strict — il n'accepte que `vDatetime` avec timezone UTC :
```python
from icalendar import vDatetime
from datetime import timezone
dt = datetime.strptime(date_str, '%d/%m/%Y').replace(tzinfo=timezone.utc)
vtodo['DTSTART'] = vDatetime(dt)  # → 20260222T000000Z ✓
```
Formats rejetés par SabreDAV : `date` Python brut, `datetime` sans timezone, `vDate`.

---

## Gestion du dépôt Git

### `.gitignore`
```
.venv/
__pycache__/
*.pyc
*.pyo
config.py
*.log
.kivy/
```

> ⚠️ `config.py` contient les credentials Nextcloud — ne jamais committer.

### `config-sample.py`
Modèle versionné pour les contributeurs. Contient URL, USERNAME, PASSWORD en exemple avec commentaires.

### Historique des commits
| Commit | Description |
|--------|-------------|
| initial | Structure de base, connexion CalDAV |
| ... | Vues ouvertes/actionnables/fermées, dates fuzzy |
| 71c4100 | Cache local, multi-tags, sous-tâches, tags affichés, fix dates CalDAV |

---

## Roadmap

### Phase 1 — Fonctionnalités core
- [x] Connexion CalDAV Nextcloud
- [x] Lecture tâches par tags (CATEGORIES)
- [x] Créer, modifier, supprimer une tâche
- [x] Marquer comme faite avec `todo.complete()`
- [x] Countdown 3 secondes avec annulation
- [x] Écran de chargement
- [x] DTSTART et DUE en lecture et édition
- [x] Dates fuzzy Bientôt/Un jour via PRIORITY CalDAV
- [x] Vue Ouvertes / Actionnables / Fermées
- [x] Sous-tâches (RELATED-TO) — lecture, création, cochage
- [x] Navigation parent ↔ enfant avec retour correct
- [x] Indice visuel ▶ sur les tâches parentes
- [x] Réinitialiser une tâche récurrente (archive + clone)
- [x] Multi-tags — saisie `tag1, tag2`, nettoyage `@`
- [x] Bouton + dans la liste des tâches d'un tag
- [x] Tags affichés dans le détail (jaune doré, depuis cache)
- [x] Tags affichés dans la liste des tâches (autres tags sous le titre)
- [x] Cache local complet — transitions fluides, zéro appel réseau dans les écrans
- [x] Fix dates CalDAV — vDatetime UTC pour SabreDAV/Nextcloud
- [x] Rechargement immédiat après édition (données fraîches dans detail)
- [x] .gitignore + config-sample.py
- [ ] Statuts complets (Actif, Différé, À faire, Inactif)

### Phase 2 — Fonctionnalités avancées
- [ ] Optimisation chargement initial (connexion persistante, fetch partiel)
- [ ] Compteur X/X tâches réalisées par tag
- [ ] Poids en temps (durée estimée)
- [ ] Rappels
- [ ] Tags hiérarchiques

### Phase 3 — Design
- [ ] Interface proche de GTG desktop
- [ ] Afficher "Bientôt" au lieu de la date quand échéance < 15 jours
- [ ] Indicateur visuel Maintenant/Bientôt/Un jour dans la liste
- [ ] Icônes, couleurs, polices
- [ ] Surbrillance jaune fluo sur les tags (comme GTG desktop)

### Phase 4 — Android
- [ ] Packaging APK avec Buildozer
- [ ] Tests sur Fairphone
- [ ] Publication F-Droid

### Phase 5 — Contribution open source
- [ ] "Verrue" Debian pour synchronisation des dates fuzzy
- [ ] Patch GTG pour bidirectionnalité des dates fuzzy via CalDAV
- [ ] Soumettre Pull Request au projet getting-things-gnome/gtg

---

## Notes techniques

| Problème | Solution |
|----------|----------|
| `uid` réservé par Kivy | Utiliser `task_uid` |
| `background_color` non supporté sur Label | Utiliser `canvas.before` |
| Warning `Ical data was modified` | Inoffensif — Nextcloud ajoute DTSTAMP manquant |
| `date` réservé Python | Utiliser `date_str` |
| N appels réseau pour `has_children` | Remplacé par `_build_parents_set()` dans `fetch_all()` |
| State résiduel dans NewTaskScreen | `edit_uid` et `parent_uid` remis à `None` en premier dans `load_form()` |
| Tags GTG avec `@` | `_clean_tags()` à la lecture, `_parse_tags()` à l'écriture |
| `@DAV_gtg` tag technique | Filtré dans `_TAGS_IGNORES` |
| Multi-tags en édition | `fetch_tags_for_uid()` lit depuis `TAGS_PAR_UID` — zéro réseau |
| Transitions bloquées par appels réseau | Cache complet dans state — écrans ne font plus d'appels |
| SabreDAV rejette `date` Python brut | `vDatetime` avec `timezone.utc` obligatoire dans `update_task` |
| Détail pas mis à jour après édition | `new_task.py` retrouve la tâche dans le cache frais et recharge `detail` |
| Indentation Python | 4 espaces par niveau, jamais de tabulations |

---

## Environnement

| Élément | Version |
|---------|---------|
| Python | 3.13 |
| Kivy | 2.3.1 |
| caldav | 2.2.6 |
| Serveur CalDAV | Nextcloud (globenet.org) |
| OS dev | Debian |
| Cible | Android (Fairphone) |
| Distribution | F-Droid (objectif) |

---

## Dépôt Git

```
https://github.com/pentux-GitHub/gtgDroid
```
