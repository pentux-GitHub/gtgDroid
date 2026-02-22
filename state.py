PAR_TAG = {}           # dict {tag: [tuple_tâche, ...]} — tâches ouvertes (NEEDS-ACTION)
PAR_TAG_CLOSED = {}    # dict {tag: [tuple_tâche, ...]} — tâches faites (COMPLETED)
PAR_TAG_DISMISSED = {} # dict {tag: [tuple_tâche, ...]} — tâches abandonnées (CANCELLED)
CURRENT_TAG = ''       # tag sélectionné en cours
CURRENT_VIEW = 'open'  # vue active : 'open', 'actionable', 'closed', 'dismissed'

# Cache local — chargé une seule fois au démarrage via fetch_all()
TAGS_PAR_UID = {}      # {task_uid: "IT, urgent"} — tous les tags d'une tâche
SUBTASKS_PAR_UID = {}  # {task_uid: [tuple_tâche, ...]} — sous-tâches triées A→Z