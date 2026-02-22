from dataclasses import dataclass, field


@dataclass
class Task:
    """Modèle de données d'une tâche gtgDroid.

    Remplace le tuple (title, status, due_str, start_str, description,
    task_uid, priority, has_children) utilisé en Phase 1.

    Accès par attribut au lieu d'index — lisible, extensible, sans risque
    de casser le code existant quand on ajoute un champ.
    """
    title: str
    status: str                  # 'NEEDS-ACTION', 'COMPLETED', 'CANCELLED'
    due_str: str                 # 'JJ/MM/AAAA' ou ''
    start_str: str               # 'JJ/MM/AAAA' ou ''
    description: str             # Notes libres
    task_uid: str                # UUID CalDAV
    priority: int                # 0=Maintenant, 5=Bientôt, 9=Un jour
    has_children: bool           # True si la tâche a des sous-tâches
    fuzzy: str = ''              # 'soon', 'someday', '' — X-GTG-FUZZY CalDAV
    tags: str = ''               # 'IT, urgent' — copie locale pour accès rapide

    def is_completed(self) -> bool:
        return self.status == 'COMPLETED'

    def is_cancelled(self) -> bool:
        return self.status == 'CANCELLED'

    def is_open(self) -> bool:
        return self.status == 'NEEDS-ACTION'

    def priority_label(self) -> str:
        if self.priority == 5 or self.fuzzy == 'soon':
            return 'Bientôt'
        if self.priority == 9 or self.fuzzy == 'someday':
            return 'Un jour'
        return ''

    def priority_color(self):
        label = self.priority_label()
        if label == 'Bientôt':
            return (0.5, 0.4, 0.8, 1)
        if label == 'Un jour':
            return (0.5, 0.5, 0.5, 1)
        return (0.3, 0.3, 0.3, 1)
