import caldav
from icalendar import Calendar, Todo
from datetime import datetime
import uuid
from collections import defaultdict
from config import URL, USERNAME, PASSWORD
from models import Task
import state


def get_client():
    return caldav.DAVClient(url=URL, username=USERNAME, password=PASSWORD)


# Tags à ignorer — ajoutés automatiquement par GTG
_TAGS_IGNORES = {'DAV_gtg', '@DAV_gtg'}


def _clean_tags(tags):
    """
    Nettoie la liste des tags :
    - Retire le @ en début de tag
    - Filtre les tags techniques de GTG (DAV_gtg)
    - Retourne ['Sans tag'] si la liste est vide après nettoyage
    """
    result = []
    for t in tags:
        t_clean = t.lstrip('@')
        if t_clean and t_clean not in _TAGS_IGNORES:
            result.append(t_clean)
    return result if result else ['Sans tag']


def _parse_tags(tag_str):
    """
    Convertit une saisie utilisateur 'IT, urgent, @perso'
    en liste propre ['IT', 'urgent', 'perso'].
    """
    if not tag_str or not tag_str.strip():
        return []
    parts = [t.strip().lstrip('@') for t in tag_str.split(',')]
    return [t for t in parts if t and t not in _TAGS_IGNORES]


def fetch_all():
    """
    Fetch principal — UN SEUL passage sur Nextcloud.
    Remplit simultanément :
      - state.PAR_TAG          (tâches ouvertes par tag)
      - state.PAR_TAG_CLOSED   (tâches fermées par tag)
      - state.TAGS_PAR_UID     (tous les tags par uid)
      - state.SUBTASKS_PAR_UID (sous-tâches par uid parent)
    Zéro appel réseau supplémentaire nécessaire dans les écrans.
    """
    principal = get_client().principal()

    par_tag = defaultdict(list)
    par_tag_closed = defaultdict(list)
    par_tag_dismissed = defaultdict(list)
    tags_par_uid = {}
    subtasks_raw = defaultdict(list)  # {parent_uid: [vtodo, ...]}

    # Passage unique sur TOUTES les tâches
    all_vtodos = []
    for calendar in principal.calendars():
        for todo in calendar.todos(include_completed=True):
            ical = todo.icalendar_instance
            vtodo = ical.walk('VTODO')[0]
            all_vtodos.append(vtodo)

    # Étape 1 : identifier les parents et regrouper les sous-tâches
    parents_set = set()
    for vtodo in all_vtodos:
        related = vtodo.get('RELATED-TO', None)
        if related:
            parent_uid = str(related)
            parents_set.add(parent_uid)
            subtasks_raw[parent_uid].append(vtodo)

    # Étape 2 : construire les objets Task et remplir PAR_TAG, PAR_TAG_CLOSED, TAGS_PAR_UID
    for vtodo in all_vtodos:
        title = str(vtodo.get('SUMMARY', 'Sans titre'))
        status = str(vtodo.get('STATUS', 'NEEDS-ACTION'))
        due = vtodo.get('DUE', None)
        due_str = due.dt.strftime('%d/%m/%Y') if due else ''
        start = vtodo.get('DTSTART', None)
        start_str = start.dt.strftime('%d/%m/%Y') if start else ''
        description = str(vtodo.get('DESCRIPTION', ''))
        task_uid = str(vtodo.get('UID', ''))
        priority = int(vtodo.get('PRIORITY', 0))
        fuzzy = str(vtodo.get('X-GTG-FUZZY', ''))
        categories = vtodo.get('CATEGORIES', None)
        tags = [str(c) for c in categories.cats] if categories else []
        tags_clean = _clean_tags(tags)
        has_children = task_uid in parents_set

        # Cache tags par uid — string "IT, urgent"
        tags_str = ', '.join(t for t in tags_clean if t != 'Sans tag')
        tags_par_uid[task_uid] = tags_str

        task = Task(
            title=title,
            status=status,
            due_str=due_str,
            start_str=start_str,
            description=description,
            task_uid=task_uid,
            priority=priority,
            has_children=has_children,
            fuzzy=fuzzy,
            tags=tags_str
        )

        if status == 'COMPLETED':
            for tag in tags_clean:
                par_tag_closed[tag].append(task)
        elif status == 'CANCELLED':
            for tag in tags_clean:
                par_tag_dismissed[tag].append(task)
        else:
            for tag in tags_clean:
                par_tag[tag].append(task)

    # Étape 3 : construire le cache des sous-tâches triées A→Z
    subtasks_par_uid = {}
    for parent_uid, vtodo_list in subtasks_raw.items():
        subtasks = []
        for vtodo in vtodo_list:
            title = str(vtodo.get('SUMMARY', 'Sans titre'))
            status = str(vtodo.get('STATUS', 'NEEDS-ACTION'))
            due = vtodo.get('DUE', None)
            due_str = due.dt.strftime('%d/%m/%Y') if due else ''
            start = vtodo.get('DTSTART', None)
            start_str = start.dt.strftime('%d/%m/%Y') if start else ''
            description = str(vtodo.get('DESCRIPTION', ''))
            task_uid = str(vtodo.get('UID', ''))
            priority = int(vtodo.get('PRIORITY', 0))
            fuzzy = str(vtodo.get('X-GTG-FUZZY', ''))
            has_children = task_uid in parents_set
            subtasks.append(Task(
                title=title, status=status, due_str=due_str,
                start_str=start_str, description=description,
                task_uid=task_uid, priority=priority,
                has_children=has_children, fuzzy=fuzzy
            ))
        subtasks.sort(key=lambda t: t.title)
        subtasks_par_uid[parent_uid] = subtasks

    # Mise à jour atomique du state
    state.PAR_TAG = dict(par_tag)
    state.PAR_TAG_CLOSED = dict(par_tag_closed)
    state.PAR_TAG_DISMISSED = dict(par_tag_dismissed)
    state.TAGS_PAR_UID = tags_par_uid
    state.SUBTASKS_PAR_UID = subtasks_par_uid


def fetch_tasks():
    """Appelle fetch_all() et retourne PAR_TAG."""
    fetch_all()
    return state.PAR_TAG


def fetch_tasks_completed():
    """Retourne PAR_TAG_CLOSED — déjà rempli par fetch_all()."""
    return state.PAR_TAG_CLOSED


def fetch_subtasks(parent_uid):
    """Retourne les sous-tâches depuis le cache — zéro appel réseau."""
    return state.SUBTASKS_PAR_UID.get(parent_uid, [])


def fetch_tags_for_uid(task_uid):
    """Retourne les tags depuis le cache — zéro appel réseau."""
    return state.TAGS_PAR_UID.get(task_uid, '')


def mark_as_done(task_uid):
    principal = get_client().principal()
    for calendar in principal.calendars():
        for todo in calendar.todos(include_completed=False):
            ical = todo.icalendar_instance
            vtodo = ical.walk('VTODO')[0]
            if str(vtodo.get('UID', '')) == task_uid:
                todo.complete()
                return True
    return False


def dismiss_task(task_uid):
    """Abandonne une tâche — STATUS:CANCELLED, distincte de COMPLETED."""
    principal = get_client().principal()
    for calendar in principal.calendars():
        for todo in calendar.todos(include_completed=False):
            ical = todo.icalendar_instance
            vtodo = ical.walk('VTODO')[0]
            if str(vtodo.get('UID', '')) == task_uid:
                vtodo['STATUS'] = 'CANCELLED'
                todo.save()
                return True
    return False


def delete_task(task_uid):
    principal = get_client().principal()
    for calendar in principal.calendars():
        for todo in calendar.todos(include_completed=False):
            ical = todo.icalendar_instance
            vtodo = ical.walk('VTODO')[0]
            if str(vtodo.get('UID', '')) == task_uid:
                todo.delete()
                return True
    return False


def create_task(title, tags=None, start=None, due=None, description='', priority=0):
    """tags peut être une string 'IT, urgent' ou une liste ['IT', 'urgent']"""
    principal = get_client().principal()
    for calendar in principal.calendars():
        if calendar.name == 'gtg':
            new_uid = str(uuid.uuid4())
            cal = Calendar()
            cal.add('prodid', '-//gtgDroid//FR')
            cal.add('version', '2.0')
            todo = Todo()
            todo.add('uid', new_uid)
            todo.add('summary', title)
            todo.add('status', 'NEEDS-ACTION')
            todo.add('created', datetime.now())
            if description:
                todo.add('description', description)
            if isinstance(tags, str):
                tag_list = _parse_tags(tags)
            elif isinstance(tags, list):
                tag_list = [t.lstrip('@') for t in tags if t]
            else:
                tag_list = []
            if tag_list:
                todo.add('categories', tag_list)
            if start:
                todo.add('dtstart', datetime.strptime(start, '%d/%m/%Y').date())
            if due:
                todo.add('due', datetime.strptime(due, '%d/%m/%Y').date())
            if priority:
                todo.add('priority', priority)
                if priority == 5:
                    todo.add('x-gtg-fuzzy', 'soon')
                elif priority == 9:
                    todo.add('x-gtg-fuzzy', 'someday')
            cal.add_component(todo)
            calendar.add_todo(cal.to_ical().decode('utf-8'))
            return new_uid
    return None


def create_subtask(parent_uid, title, tags=None, start=None, due=None, description='', priority=0):
    """Crée une sous-tâche liée à une tâche parent via RELATED-TO."""
    principal = get_client().principal()
    for calendar in principal.calendars():
        if calendar.name == 'gtg':
            new_uid = str(uuid.uuid4())
            cal = Calendar()
            cal.add('prodid', '-//gtgDroid//FR')
            cal.add('version', '2.0')
            todo = Todo()
            todo.add('uid', new_uid)
            todo.add('summary', title)
            todo.add('status', 'NEEDS-ACTION')
            todo.add('created', datetime.now())
            todo.add('related-to', parent_uid)
            if description:
                todo.add('description', description)
            if isinstance(tags, str):
                tag_list = _parse_tags(tags)
            elif isinstance(tags, list):
                tag_list = [t.lstrip('@') for t in tags if t]
            else:
                tag_list = []
            if tag_list:
                todo.add('categories', tag_list)
            if start:
                todo.add('dtstart', datetime.strptime(start, '%d/%m/%Y').date())
            if due:
                todo.add('due', datetime.strptime(due, '%d/%m/%Y').date())
            if priority:
                todo.add('priority', priority)
                if priority == 5:
                    todo.add('x-gtg-fuzzy', 'soon')
                elif priority == 9:
                    todo.add('x-gtg-fuzzy', 'someday')
            cal.add_component(todo)
            calendar.add_todo(cal.to_ical().decode('utf-8'))
            return new_uid
    return None


def update_task(task_uid, new_title, new_tags=None, new_start=None, new_due=None, new_description='', new_priority=0):
    principal = get_client().principal()
    for calendar in principal.calendars():
        for todo in calendar.todos(include_completed=False):
            ical = todo.icalendar_instance
            vtodo = ical.walk('VTODO')[0]
            if str(vtodo.get('UID', '')) == task_uid:
                vtodo['SUMMARY'] = new_title
                if new_description:
                    vtodo['DESCRIPTION'] = new_description
                elif 'DESCRIPTION' in vtodo:
                    del vtodo['DESCRIPTION']
                if isinstance(new_tags, str):
                    tag_list = _parse_tags(new_tags)
                elif isinstance(new_tags, list):
                    tag_list = [t.lstrip('@') for t in new_tags if t]
                else:
                    tag_list = []
                if tag_list:
                    vtodo['CATEGORIES'] = ','.join(tag_list)
                elif 'CATEGORIES' in vtodo:
                    del vtodo['CATEGORIES']
                if new_start:
                    from icalendar import vDatetime
                    from datetime import timezone
                    dt = datetime.strptime(new_start, '%d/%m/%Y').replace(tzinfo=timezone.utc)
                    vtodo['DTSTART'] = vDatetime(dt)
                elif 'DTSTART' in vtodo:
                    del vtodo['DTSTART']
                if new_due:
                    from icalendar import vDatetime
                    from datetime import timezone
                    dt = datetime.strptime(new_due, '%d/%m/%Y').replace(tzinfo=timezone.utc)
                    vtodo['DUE'] = vDatetime(dt)
                elif 'DUE' in vtodo:
                    del vtodo['DUE']
                if new_priority:
                    vtodo['PRIORITY'] = new_priority
                    if new_priority == 5:
                        vtodo['X-GTG-FUZZY'] = 'soon'
                    elif new_priority == 9:
                        vtodo['X-GTG-FUZZY'] = 'someday'
                else:
                    if 'PRIORITY' in vtodo:
                        del vtodo['PRIORITY']
                    if 'X-GTG-FUZZY' in vtodo:
                        del vtodo['X-GTG-FUZZY']
                todo.save()
                return True
    return False


def reset_and_clone_task(task_uid):
    """
    Réinitialise une tâche récurrente (non cyclique) :
    - Archive la tâche et ses sous-tâches (COMPLETED)
    - Recrée une copie fraîche avec PRIORITY=9 (Un jour), sans dates
    - Recrée toutes les sous-tâches fraîches liées au nouveau parent
    """
    principal = get_client().principal()

    parent_todo = None
    parent_vtodo = None
    for calendar in principal.calendars():
        for todo in calendar.todos(include_completed=False):
            ical = todo.icalendar_instance
            vtodo = ical.walk('VTODO')[0]
            if str(vtodo.get('UID', '')) == task_uid:
                parent_todo = todo
                parent_vtodo = vtodo
                break
        if parent_todo:
            break

    if not parent_todo:
        return None

    parent_title = str(parent_vtodo.get('SUMMARY', 'Sans titre'))
    parent_description = str(parent_vtodo.get('DESCRIPTION', ''))
    parent_categories = parent_vtodo.get('CATEGORIES', None)
    parent_tags = []
    if parent_categories:
        parent_tags = _clean_tags([str(c) for c in parent_categories.cats])
        parent_tags = [t for t in parent_tags if t != 'Sans tag']

    subtasks_data = fetch_subtasks(task_uid)
    parent_todo.complete()
    for subtask in subtasks_data:
        mark_as_done(subtask.task_uid)

    new_parent_uid = create_task(
        title=parent_title,
        tags=parent_tags,
        description=parent_description if parent_description != 'None' else '',
        priority=9
    )

    if not new_parent_uid:
        return None

    for subtask in subtasks_data:
        create_subtask(
            parent_uid=new_parent_uid,
            title=subtask.title,
            tags=parent_tags,
            description=subtask.description if subtask.description != 'None' else ''
        )

    return new_parent_uid