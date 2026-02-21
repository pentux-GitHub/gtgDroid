import caldav
from icalendar import Calendar, Todo
from datetime import datetime
import uuid
from collections import defaultdict
from config import URL, USERNAME, PASSWORD

def get_client():
    return caldav.DAVClient(url=URL, username=USERNAME, password=PASSWORD)

def fetch_tasks():
    principal = get_client().principal()
    par_tag = defaultdict(list)
    for calendar in principal.calendars():
        for todo in calendar.todos(include_completed=False):
            ical = todo.icalendar_instance
            vtodo = ical.walk('VTODO')[0]
            title = str(vtodo.get('SUMMARY', 'Sans titre'))
            status = str(vtodo.get('STATUS', 'NEEDS-ACTION'))
            due = vtodo.get('DUE', None)
            due_str = due.dt.strftime('%d/%m/%Y') if due else ''
            start = vtodo.get('DTSTART', None)
            start_str = start.dt.strftime('%d/%m/%Y') if start else ''
            description = str(vtodo.get('DESCRIPTION', ''))
            task_uid = str(vtodo.get('UID', ''))
            priority = int(vtodo.get('PRIORITY', 0))
            categories = vtodo.get('CATEGORIES', None)
            tags = [str(c) for c in categories.cats] if categories else ['Sans tag']
            for tag in tags:
                par_tag[tag].append((title, status, due_str, start_str, description, task_uid, priority))
    return par_tag

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

def create_task(title, tag=None, start=None, due=None, description='', priority=0):
    from datetime import datetime
    principal = get_client().principal()
    for calendar in principal.calendars():
        if calendar.name == 'gtg':
            cal = Calendar()
            cal.add('prodid', '-//gtgDroid//FR')
            cal.add('version', '2.0')
            todo = Todo()
            todo.add('uid', str(uuid.uuid4()))
            todo.add('summary', title)
            todo.add('status', 'NEEDS-ACTION')
            todo.add('created', datetime.now())
            if description:
                todo.add('description', description)
            if tag and tag != 'Sans tag':
                todo.add('categories', [tag])
            if start:
                todo.add('dtstart', datetime.strptime(start, '%d/%m/%Y').date())
            if due:
                todo.add('due', datetime.strptime(due, '%d/%m/%Y').date())
            if priority:
                todo.add('priority', priority)
            cal.add_component(todo)
            calendar.add_todo(cal.to_ical().decode('utf-8'))
            return True
    return False

def update_task(task_uid, new_title, new_tag=None, new_start=None, new_due=None, new_description='', new_priority=0):
    from datetime import datetime
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
                if new_tag and new_tag != 'Sans tag':
                    vtodo['CATEGORIES'] = new_tag
                elif 'CATEGORIES' in vtodo:
                    del vtodo['CATEGORIES']
                if new_start:
                    vtodo['DTSTART'] = datetime.strptime(new_start, '%d/%m/%Y').date()
                elif 'DTSTART' in vtodo:
                    del vtodo['DTSTART']
                if new_due:
                    vtodo['DUE'] = datetime.strptime(new_due, '%d/%m/%Y').date()
                elif 'DUE' in vtodo:
                    del vtodo['DUE']
                if new_priority:
                    vtodo['PRIORITY'] = new_priority
                elif 'PRIORITY' in vtodo:
                    del vtodo['PRIORITY']
                todo.save()
                return True
    return False


def fetch_tasks_completed():
    principal = get_client().principal()
    par_tag = defaultdict(list)
    for calendar in principal.calendars():
        for todo in calendar.todos(include_completed=True):
            ical = todo.icalendar_instance
            vtodo = ical.walk('VTODO')[0]
            status = str(vtodo.get('STATUS', 'NEEDS-ACTION'))
            if status != 'COMPLETED':
                continue
            title = str(vtodo.get('SUMMARY', 'Sans titre'))
            due = vtodo.get('DUE', None)
            due_str = due.dt.strftime('%d/%m/%Y') if due else ''
            start = vtodo.get('DTSTART', None)
            start_str = start.dt.strftime('%d/%m/%Y') if start else ''
            description = str(vtodo.get('DESCRIPTION', ''))
            task_uid = str(vtodo.get('UID', ''))
            priority = int(vtodo.get('PRIORITY', 0))
            categories = vtodo.get('CATEGORIES', None)
            tags = [str(c) for c in categories.cats] if categories else ['Sans tag']
            for tag in tags:
                par_tag[tag].append((title, status, due_str, start_str, description, task_uid, priority))
    return par_tag