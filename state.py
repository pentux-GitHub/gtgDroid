PAR_TAG = {}          # dict {tag: [tuple_tâche, ...]} — tâches ouvertes
PAR_TAG_CLOSED = {}   # dict {tag: [tuple_tâche, ...]} — tâches fermées
CURRENT_TAG = ''      # tag sélectionné en cours
CURRENT_VIEW = 'open' # vue active : 'open', 'actionable', 'closed'

# Cache local — chargé une seule fois au démarrage, zéro appel réseau dans les écrans
TAGS_PAR_UID = {}     # {task_uid: "IT, urgent"} — tous les tags d'une tâche
SUBTASKS_PAR_UID = {} # {task_uid: [tuple_tâche, ...]} — sous-tâches triées A→Z