# gtgDroid — Journal de développement

## Vision
Application Android de gestion de tâches GTD, clone mobile de GTG (Getting Things GNOME),
synchronisée via CalDAV avec Nextcloud. Objectif final : publier sur F-Droid.

---

## Architecture actuelle

```
gtgDroid/
├── main.py              # App Kivy + ScreenManager (20 lignes)
├── caldav_api.py        # Toute la logique CalDAV (fetch, create, update, delete)
├── state.py             # Variables globales (PAR_TAG, PAR_TAG_CLOSED, CURRENT_TAG, CURRENT_VIEW)
├── widgets.py           # Composants réutilisables (confirm_popup, loading_popup)
├── config.py            # URL, USERNAME, PASSWORD Nextcloud
├── screens/
│   ├── __init__.py
│   ├── loading.py       # Écran de chargement au démarrage
│   ├── tags.py          # Liste des tags avec compteur + boutons de vue
│   ├── tasks.py         # Liste des tâches d'un tag
│   ├── detail.py        # Détail d'une tâche
│   └── new_task.py      # Formulaire création/modification
├── Suivi/
│   ├── gtgDroid.md      # Ce fichier
│   └── GTGDroid_vision.md
└── .venv/               # Python 3.13, Kivy 2.3.1, caldav 2.2.6
```

**Tuple tâche (7 éléments) :**
`(title, status, due_str, start_str, description, task_uid, priority)`

**Variables globales (state.py) :**
```python
PAR_TAG = {}          # tâches ouvertes groupées par tag
PAR_TAG_CLOSED = {}   # tâches fermées groupées par tag
CURRENT_TAG = ''      # tag sélectionné
CURRENT_VIEW = 'open' # vue active : 'open', 'actionable', 'closed'
```

---

## Fonctionnalités implémentées ✅

### Navigation
- 5 écrans avec transitions SlideTransition
- LoadingScreen → TagsScreen → TasksScreen → DetailScreen → NewTaskScreen
- Bouton Retour avec annulation automatique des événements Clock en cours

### Vues (comme GTG desktop)
- **Ouvertes** — toutes les tâches non complétées
- **Actionnables** — tâches sans DTSTART dans le futur et sans PRIORITY=9
- **Fermées** — tâches COMPLETED
- Boutons de vue avec surbrillance du bouton actif
- Filtrage conservé lors de la navigation entre tags

### Lecture CalDAV
- Connexion Nextcloud via caldav 2.2.6
- Lecture tâches groupées par tags (CATEGORIES)
- Lecture SUMMARY, STATUS, DUE, DTSTART, DESCRIPTION, UID, PRIORITY
- `fetch_tasks()` — tâches ouvertes
- `fetch_tasks_completed()` — tâches fermées
- Rafraîchissement manuel avec popup "Actualisation en cours"
- Rafraîchissement automatique après toute modification

### Création de tâche
- Titre (obligatoire)
- Tag (optionnel)
- Commence le : champ texte JJ/MM/AAAA + bouton Aujourd'hui
- Échéance : champ texte JJ/MM/AAAA + bouton Aujourd'hui
- Quand : 3 boutons Maintenant / Bientôt / Un jour (via PRIORITY CalDAV)
- Notes (optionnel)

### Modification de tâche
- Formulaire pré-rempli avec toutes les données existantes
- Bouton Modifier dans le header de DetailScreen
- Retour vers DetailScreen après modification

### Suppression de tâche
- Bouton rouge Supprimer dans le header de DetailScreen
- Confirmation popup avant suppression
- Retour vers TasksScreen après suppression

### Marquer comme faite
- Utilise `todo.complete()` — validé, ne supprime pas la tâche
- Confirmation popup
- Compte à rebours 3 secondes avec bouton Annuler orange
- Retour vers TasksScreen après validation

---

## Gestion des dates fuzzy — Point technique important

### Problème identifié
GTG desktop stocke les dates fuzzy en texte brut dans son XML local :
```xml
<due>soon</due>
<due>someday</due>
```
Ces valeurs ne sont **pas synchronisées vers CalDAV/Nextcloud** — GTG les perd à la synchro.
C'est une limitation connue et documentée de GTG lui-même.

### Solution adoptée : champ PRIORITY CalDAV
Pour distinguer "Bientôt" et "Un jour" via CalDAV, on utilise le champ standard PRIORITY :

| Bouton gtgDroid | PRIORITY CalDAV | Affiché dans GTG desktop |
|-----------------|-----------------|--------------------------|
| Maintenant      | 0 (aucune)      | Pas de date              |
| Bientôt         | 5               | Pas de date (ignoré)     |
| Un jour         | 9               | Pas de date (ignoré)     |

**Avantages :** champ standard CalDAV, supporté par tasks.org, transparent pour GTG (pas d'effet de bord).

**Limitation actuelle :** GTG desktop ne lit pas PRIORITY pour ses dates fuzzy → pas de bidirectionnalité.

### Piste future : "verrue" Debian
Un petit script sur le PC Debian qui surveille les changements CalDAV et réécrit
le XML GTG local avec `soon`/`someday` quand il détecte PRIORITY=5/9.
Simple, léger, sans toucher à GTG ni à gtgDroid.

### Piste future : patch GTG open source
Contribuer un patch au projet GTG (getting-things-gnome/gtg sur GitHub) :
- `PRIORITY=5` lu depuis CalDAV → stocker `<due>soon</due>` dans le XML local
- `PRIORITY=9` lu depuis CalDAV → stocker `<due>someday</due>` dans le XML local

**Approche recommandée :**
1. Cloner GTG depuis GitHub
2. Créer une instance de test isolée : `./launch.sh -s test_gtgdroid`
3. Modifier le backend CalDAV de GTG (dans GTG/backends/)
4. Tester sans toucher les données de production
5. Soumettre un Pull Request au projet GTG

---

## Roadmap

### Phase 1 — Fonctionnalités core (en cours)
- [x] Connexion CalDAV Nextcloud
- [x] Lecture tâches par tags
- [x] Créer, modifier, supprimer une tâche
- [x] Marquer comme faite avec todo.complete()
- [x] Countdown 3 secondes avec annulation
- [x] Écran de chargement
- [x] DTSTART et DUE en lecture et édition
- [x] Dates fuzzy Bientôt/Un jour via PRIORITY CalDAV
- [x] Vue Ouvertes / Actionnables / Fermées
- [ ] Sous-tâches (RELATED-TO CalDAV)
- [ ] Statuts complets (Actif, Différé, A faire, Inactif)
- [ ] Tâches récurrentes (RRULE)

### Phase 2 — Fonctionnalités avancées
- [ ] Compteur X/X tâches réalisées par tag
- [ ] Poids en temps (durée estimée) pour alimenter l'agenda
- [ ] Rappels
- [ ] Tags hiérarchiques

### Phase 3 — Design
- [ ] Interface proche de GTG desktop
- [ ] Afficher "Bientôt" au lieu de la date quand échéance < 15 jours
- [ ] Indicateur visuel Maintenant/Bientôt/Un jour dans la liste des tâches
- [ ] Icônes, couleurs, polices

### Phase 4 — Android
- [ ] Packaging APK avec Buildozer
- [ ] Tests sur Fairphone
- [ ] Publication F-Droid

### Phase 5 — Contribution open source
- [ ] "Verrue" Debian pour synchronisation fuzzy dates
- [ ] Patch GTG pour bidirectionnalité des dates fuzzy via CalDAV
- [ ] Soumettre Pull Request au projet getting-things-gnome/gtg

---

## Notes techniques

- `uid` est un attribut réservé par Kivy → utiliser `task_uid`
- `background_color` non supporté sur Label → utiliser canvas.before
- Warning `Ical data was modified` inoffensif — Nextcloud ajoute DTSTAMP manquant
- Connexion CalDAV non cachée — nouvelle instance à chaque fetch pour données fraîches
- Lenteur réseau normale — plusieurs fetch CalDAV par action, optimisation future
- GTG desktop ignore PRIORITY CalDAV pour ses dates fuzzy (limitation GTG)
- tasks.org synchronise PRIORITY via CalDAV nativement
- Indentation Python critique : 4 espaces par niveau, pas de mélange espaces/tabulations
- `date` est un nom réservé Python → utiliser `date_str` pour les variables locales
- `fetch_tasks_completed()` doit être au niveau 0 dans caldav_api.py (pas imbriquée)

---

## Lancer l'application

```bash
cd /home/pentux/Documents/IT/gtgDroid
source .venv/bin/activate
python3 main.py
```
