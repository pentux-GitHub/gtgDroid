# gtgDroid — Journal de développement

## Vision

Application Android de gestion de tâches GTD, clone mobile de GTG (Getting Things GNOME), synchronisée via CalDAV avec Nextcloud. Objectif final : publier sur F-Droid avec une qualité et une expérience utilisateur équivalente aux meilleures apps propriétaires.

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
├── .gitignore
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

---

## Modèle de données

### Tuple tâche (8 éléments) — à migrer vers dataclass

```python
(title, status, due_str, start_str, description, task_uid, priority, has_children)
#  [0]    [1]     [2]      [3]         [4]          [5]       [6]       [7]
```

> ⚠️ Le tuple est fragile — ajouter un champ impose de modifier tous les endroits qui le dépackent. Migration vers `dataclass` planifiée en Phase 2 (voir roadmap).

### Variables globales et cache (`state.py`)

```python
PAR_TAG = {}           # tâches ouvertes (NEEDS-ACTION) groupées par tag
PAR_TAG_CLOSED = {}    # tâches faites (COMPLETED) groupées par tag
PAR_TAG_DISMISSED = {} # tâches abandonnées (CANCELLED) groupées par tag
CURRENT_TAG = ''
CURRENT_VIEW = 'open'  # 'open', 'actionable', 'closed', 'dismissed'

# Cache local — zéro appel réseau dans les écrans
TAGS_PAR_UID = {}      # {uid: "IT, urgent"}
SUBTASKS_PAR_UID = {}  # {uid: [tuple, ...]}
```

---

## Architecture réseau

`fetch_all()` fait **un seul passage** sur Nextcloud au démarrage et remplit tout `state`. Zéro appel réseau dans les écrans — uniquement à l'écriture, suivi d'un `fetch_all()` pour resynchroniser.

### Performances validées (140 tâches, Nextcloud distant)
- Chargement initial : ~8 secondes
- Navigation : instantanée
- Transitions : fluides

---

## Statuts des tâches

| Statut CalDAV | Bouton gtgDroid | Vue | Compte dans stats |
|---------------|-----------------|-----|-------------------|
| NEEDS-ACTION | — | Ouvertes / Actionnables | — |
| COMPLETED | ✓ Marquer comme faite | Fermées | ✅ Oui |
| CANCELLED | ✕ Abandonner | Abandonnées | ❌ Non |

---

## Gestion des dates fuzzy

### Problème
GTG stocke `soon`/`someday` en XML local, non synchronisé CalDAV. La synchro GTG → Nextcloud perd cette information.

### Solution actuelle : PRIORITY CalDAV
| Bouton | PRIORITY | GTG desktop |
|--------|----------|-------------|
| Maintenant | 0 | Pas de date |
| Bientôt | 5 | Ignoré |
| Un jour | 9 | Ignoré |

### Piste retenue pour la suite : champ X-GTG-FUZZY (Option C)
Stocker en parallèle un champ CalDAV personnalisé :
```
X-GTG-FUZZY:soon
X-GTG-FUZZY:someday
```
**Avantages :**
- GTG l'ignore silencieusement (standard CalDAV — les champs `X-` inconnus sont préservés)
- Pas d'effet de bord sur les autres clients (tasks.org, etc.)
- Base propre pour un futur patch GTG qui lirait ce champ
- On garde PRIORITY en parallèle pour tasks.org

**Ce que ça change dans le code :**
- `create_task()` et `update_task()` : écrire `X-GTG-FUZZY` selon le bouton choisi
- `fetch_all()` : lire `X-GTG-FUZZY` et le stocker dans le tuple/dataclass
- Affichage : montrer "Bientôt" / "Un jour" depuis ce champ plutôt que PRIORITY

---

## Points techniques à anticiper

### A — Historique grandissant
`fetch_all()` charge toutes les tâches y compris COMPLETED et CANCELLED. Dans 2 ans avec 2000+ tâches archivées, le chargement va exploser.
**Solution future :** charger l'historique à la demande (bouton "Charger plus"), ou limiter à une fenêtre temporelle (ex : 90 jours).

### B — Conflits de synchro
Si une tâche est modifiée simultanément sur GTG desktop et gtgDroid, le dernier à écrire gagne silencieusement. Comportement identique à GTG lui-même — acceptable, mais à documenter dans le README.

### C — Tuple fragile → dataclass
Chaque nouveau champ impose de modifier tous les endroits qui dépackent le tuple. Avec `dataclass` :
```python
@dataclass
class Task:
    title: str
    status: str
    due_str: str
    start_str: str
    description: str
    task_uid: str
    priority: int
    has_children: bool
    fuzzy: str = ''  # 'soon', 'someday', ''
```
Ajouter un champ devient anodin — les anciens accès ne cassent pas.

### D — dismiss_task() et include_completed
`dismiss_task()` cherche dans `todos(include_completed=False)`. Le comportement de la lib caldav sur les tâches `CANCELLED` avec ce filtre est à vérifier — impact sur la future fonction "Ré-ouvrir une tâche".

### E — Pas de "Ré-ouvrir une tâche"
Actuellement impossible de rouvrir une tâche fermée ou abandonnée. Fonctionnalité GTG importante pour la mémoire — à implémenter dans la vue Fermées et Abandonnées.

---

## Roadmap détaillée

### Phase 1 — Fonctionnalités core ✅ COMPLÈTE

- [x] Connexion CalDAV Nextcloud
- [x] Lecture tâches par tags (CATEGORIES)
- [x] Créer, modifier, supprimer une tâche
- [x] Marquer comme faite avec `todo.complete()`
- [x] Countdown 3 secondes avec annulation
- [x] Écran de chargement
- [x] DTSTART et DUE en lecture et édition
- [x] Dates fuzzy Bientôt/Un jour via PRIORITY CalDAV
- [x] Vue Ouvertes / Actionnables / Fermées / Abandonnées
- [x] Sous-tâches (RELATED-TO) — lecture, création, cochage
- [x] Navigation parent ↔ enfant avec retour correct à n'importe quelle profondeur
- [x] Indice visuel ▶ sur les tâches parentes
- [x] Réinitialiser une tâche récurrente (archive + clone)
- [x] Multi-tags — saisie `tag1, tag2`, nettoyage `@`
- [x] Bouton + dans la liste des tâches et des tags
- [x] Tags affichés dans le détail (jaune doré) et dans la liste des tâches
- [x] Cache local complet — transitions fluides, zéro appel réseau dans les écrans
- [x] Fix dates CalDAV — vDatetime UTC pour SabreDAV/Nextcloud
- [x] Rechargement immédiat après édition
- [x] Statut Abandonné (CANCELLED) distinct de Terminé (COMPLETED)
- [x] .gitignore + config-sample.py

---

### Phase 2 — Robustesse et fonctionnalités avancées

#### 2.1 — Refactoring dataclass (priorité haute)
**Pourquoi maintenant :** avant d'ajouter des champs (fuzzy, durée...), migrer le tuple vers dataclass évite une dette technique explosive.
- [ ] Créer `models.py` avec `@dataclass Task`
- [ ] Migrer `fetch_all()` pour retourner des `Task`
- [ ] Mettre à jour tous les écrans (accès par attribut au lieu d'index)
- [ ] Tests de non-régression

#### 2.2 — Dates fuzzy propres (X-GTG-FUZZY)
- [ ] Écrire `X-GTG-FUZZY:soon/someday` dans `create_task()` et `update_task()`
- [ ] Lire `X-GTG-FUZZY` dans `fetch_all()` → stocker dans `Task.fuzzy`
- [ ] Afficher "Bientôt" / "Un jour" depuis `Task.fuzzy` dans le détail et la liste
- [ ] Garder PRIORITY en parallèle pour tasks.org

#### 2.3 — Ré-ouvrir une tâche
- [ ] Bouton "Ré-ouvrir" dans le détail des tâches Fermées et Abandonnées
- [ ] `reopen_task(uid)` dans `caldav_api.py` → `STATUS:NEEDS-ACTION`
- [ ] Vérifier comportement de `todos(include_completed=False)` avec CANCELLED

#### 2.4 — Gamification et stats
- [ ] Compteur "X tâches faites aujourd'hui" dans le header de TagsScreen
- [ ] Objectif journalier configurable (5 tâches par défaut)
- [ ] Compteur X/X par tag (tâches faites / total)
- [ ] Les tâches CANCELLED ne comptent PAS dans les stats

#### 2.5 — Optimisation chargement historique
- [ ] Séparer le fetch initial (ouvertes) du fetch historique (fermées + abandonnées)
- [ ] Charger l'historique à la demande depuis les vues Fermées/Abandonnées
- [ ] Objectif : chargement initial < 3 secondes

#### 2.6 — Poids en temps
- [ ] Champ "Durée estimée" dans le formulaire (DURATION CalDAV)
- [ ] Affichage dans le détail
- [ ] Total de temps par tag (pour alimenter l'agenda)

---

### Phase 3 — Design et UX

#### 3.1 — Lisibilité et hiérarchie visuelle
- [ ] Indicateur visuel Maintenant / Bientôt / Un jour dans la liste des tâches (couleur ou icône)
- [ ] Afficher "Bientôt" au lieu de la date quand échéance < 15 jours
- [ ] Tags en surbrillance style GTG (fond coloré) dans le détail
- [ ] Meilleure distinction visuelle entre tâches parentes et enfants

#### 3.2 — Interface proche de GTG desktop
- [ ] Couleurs cohérentes avec GTG (palette GTG)
- [ ] Support des emojis sur les tags (ex : 🏠 Home, 💻 IT)
- [ ] Polices et tailles harmonisées
- [ ] Icônes métier (pas les boutons Kivy par défaut)

#### 3.3 — Confort mobile
- [ ] Swipe gauche sur une tâche → Abandonner
- [ ] Swipe droit sur une tâche → Marquer comme faite
- [ ] Scroll infini (lazy loading) pour les longues listes
- [ ] Mode paysage supporté

#### 3.4 — Rappels
- [ ] Champ rappel dans le formulaire (VALARM CalDAV)
- [ ] Notification Android au moment du rappel

---

### Phase 4 — Android

- [ ] Packaging APK avec Buildozer
- [ ] `buildozer.spec` configuré (permissions réseau, notifications)
- [ ] Tests sur Fairphone (résolution, tactile, performances)
- [ ] Icône de l'application
- [ ] Écran de démarrage (splash screen)
- [ ] Publication sur F-Droid
- [ ] README complet pour les contributeurs

---

### Phase 5 — Contribution open source GTG

- [ ] **Vue "Abandonnées" dans GTG desktop** — GTG gère `STATUS:CANCELLED` en écriture mais n'a pas de vue dédiée. Contribuer une vue "Dismissed" qui lit les tâches `CANCELLED` depuis CalDAV. Important pour la mémoire et la gamification (ne pas mélanger avec les tâches faites).
- [ ] **Patch dates fuzzy** — GTG lire `X-GTG-FUZZY:soon/someday` depuis CalDAV et écrire `<due>soon</due>` dans son XML local. Bidirectionnalité complète.
- [ ] **"Verrue" Debian** — alternative au patch GTG : script externe qui surveille CalDAV et réécrit le XML GTG local.
- [ ] Soumettre Pull Requests au projet getting-things-gnome/gtg

---

## Notes techniques

| Problème | Solution |
|----------|----------|
| `uid` réservé par Kivy | Utiliser `task_uid` |
| `background_color` non supporté sur Label | Utiliser `canvas.before` |
| Warning `Ical data was modified` | Inoffensif — Nextcloud ajoute DTSTAMP |
| `date` réservé Python | Utiliser `date_str` |
| N appels réseau pour `has_children` | `_build_parents_set()` dans `fetch_all()` |
| State résiduel dans NewTaskScreen | `edit_uid` et `parent_uid` remis à `None` en premier |
| Tags GTG avec `@` | `_clean_tags()` lecture, `_parse_tags()` écriture |
| `@DAV_gtg` tag technique | Filtré dans `_TAGS_IGNORES` |
| Transitions bloquées | Cache complet dans state |
| SabreDAV rejette `date` Python | `vDatetime` avec `timezone.utc` dans `update_task` |
| Détail pas mis à jour après édition | Retrouver la tâche dans le cache frais |
| `dismiss_task()` et CANCELLED | À vérifier avec `include_completed=False` |

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
