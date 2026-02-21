from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.core.window import Window
from kivy.clock import Clock
import caldav
from icalendar import Calendar, Todo
from datetime import datetime
import uuid
from collections import defaultdict
from config import URL, USERNAME, PASSWORD

Window.clearcolor = (0.95, 0.95, 0.95, 1)

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
            description = str(vtodo.get('DESCRIPTION', ''))
            task_uid = str(vtodo.get('UID', ''))
            categories = vtodo.get('CATEGORIES', None)
            tags = [str(c) for c in categories.cats] if categories else ['Sans tag']
            for tag in tags:
                par_tag[tag].append((title, status, due_str, description, task_uid))
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

def create_task(title, tag=None, description=''):
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
            cal.add_component(todo)
            calendar.add_todo(cal.to_ical().decode('utf-8'))
            return True
    return False

def update_task(task_uid, new_title, new_tag=None, new_description=''):
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
                todo.save()
                return True
    return False

PAR_TAG = {}
CURRENT_TAG = ''

def confirm_popup(message, on_confirm):
    content = BoxLayout(orientation='vertical', padding=10, spacing=10)
    content.add_widget(Label(text=message, halign='center'))
    buttons = BoxLayout(size_hint_y=None, height=45, spacing=10)
    popup = Popup(
        title='Confirmation',
        content=content,
        size_hint=(0.8, 0.35),
        auto_dismiss=False
    )
    btn_oui = Button(text='Oui', background_color=(0.8, 0.2, 0.2, 1), color=(1, 1, 1, 1))
    btn_non = Button(text='Non', background_color=(0.4, 0.4, 0.4, 1), color=(1, 1, 1, 1))
    def do_confirm(x):
        popup.dismiss()
        on_confirm()
    btn_oui.bind(on_press=do_confirm)
    btn_non.bind(on_press=popup.dismiss)
    buttons.add_widget(btn_oui)
    buttons.add_widget(btn_non)
    content.add_widget(buttons)
    popup.open()

def loading_popup():
    content = BoxLayout(orientation='vertical', padding=10)
    content.add_widget(Label(text='Actualisation en cours...', halign='center'))
    popup = Popup(
        title='',
        content=content,
        size_hint=(0.6, 0.2),
        auto_dismiss=False
    )
    popup.open()
    return popup

class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(
            text='gtgDroid',
            bold=True, font_size=28,
            color=(0.2, 0.5, 0.9, 1)
        ))
        self.status = Label(
            text='Connexion a Nextcloud...',
            font_size=15,
            color=(0.4, 0.4, 0.4, 1)
        )
        layout.add_widget(self.status)
        self.add_widget(layout)

    def on_enter(self):
        Clock.schedule_once(self.load_data, 0.3)

    def load_data(self, dt):
        self.status.text = 'Chargement des taches...'
        Clock.schedule_once(self._do_fetch, 0.1)

    def _do_fetch(self, dt):
        global PAR_TAG
        PAR_TAG = fetch_tasks()
        self.manager.get_screen('tags').build_ui()
        self.manager.transition.direction = 'left'
        self.manager.current = 'tags'

class TagsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation='vertical')

        header = BoxLayout(size_hint_y=None, height=55, padding=[5, 5])
        header.add_widget(Label(
            text='gtgDroid',
            bold=True, font_size=22,
            color=(0.2, 0.5, 0.9, 1)
        ))
        btn_refresh = Button(
            text='Rafraichir',
            size_hint_x=0.35,
            background_color=(0.2, 0.5, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=13
        )
        btn_refresh.bind(on_press=self.refresh)
        btn_new = Button(
            text='  +  ',
            size_hint_x=0.15,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=20,
            bold=True
        )
        btn_new.bind(on_press=self.go_to_new)
        header.add_widget(btn_refresh)
        header.add_widget(btn_new)
        root.add_widget(header)

        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=3, size_hint_y=None, padding=[10, 5])
        layout.bind(minimum_height=layout.setter('height'))

        for tag in sorted(PAR_TAG.keys()):
            nb = len(PAR_TAG[tag])
            btn = Button(
                text=f"  #{tag}  ({nb})",
                size_hint_y=None, height=55,
                halign='left',
                background_color=(1, 1, 1, 1),
                color=(0.2, 0.5, 0.9, 1),
                font_size=16,
                bold=True
            )
            btn.tag = tag
            btn.bind(on_press=self.go_to_tasks)
            layout.add_widget(btn)

        scroll.add_widget(layout)
        root.add_widget(scroll)
        self.add_widget(root)

    def refresh(self, *args):
        popup = loading_popup()
        def do_refresh(dt):
            global PAR_TAG
            PAR_TAG = fetch_tasks()
            popup.dismiss()
            self.build_ui()
        Clock.schedule_once(do_refresh, 0.1)

    def go_to_tasks(self, btn):
        global CURRENT_TAG
        CURRENT_TAG = btn.tag
        self.manager.transition.direction = 'left'
        self.manager.get_screen('tasks').load_tag(btn.tag)
        self.manager.current = 'tasks'

    def go_to_new(self, btn):
        self.manager.transition.direction = 'left'
        self.manager.get_screen('new').load_form()
        self.manager.current = 'new'

class TasksScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root = BoxLayout(orientation='vertical')
        self.add_widget(self.root)

    def load_tag(self, tag):
        self.root.clear_widgets()

        header = BoxLayout(size_hint_y=None, height=55, padding=[5, 5])
        btn_back = Button(
            text='< Retour',
            size_hint_x=0.3,
            background_color=(0.2, 0.5, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        def go_back(x):
            self.manager.transition.direction = 'right'
            self.manager.current = 'tags'
        btn_back.bind(on_press=go_back)
        header.add_widget(btn_back)
        header.add_widget(Label(
            text=f"#{tag}",
            bold=True, font_size=18,
            color=(0.2, 0.5, 0.9, 1)
        ))
        self.root.add_widget(header)

        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=2, size_hint_y=None, padding=[10, 5])
        layout.bind(minimum_height=layout.setter('height'))

        taches = sorted(PAR_TAG[tag], key=lambda x: x[2] or 'zzz')
        for title_task, status, due_str, description, task_uid in taches:
            icone = 'OK' if status == 'COMPLETED' else 'o'
            date = f"   {due_str}" if due_str else ''
            btn = Button(
                text=f"  {icone}  {title_task}{date}",
                size_hint_y=None, height=50,
                halign='left',
                background_color=(1, 1, 1, 1),
                color=(0.1, 0.1, 0.1, 1),
                font_size=15
            )
            btn.task_data = (title_task, status, due_str, description, task_uid)
            btn.bind(on_press=self.go_to_detail)
            layout.add_widget(btn)

        scroll.add_widget(layout)
        self.root.add_widget(scroll)

    def go_to_detail(self, btn):
        self.manager.transition.direction = 'left'
        self.manager.get_screen('detail').load_task(btn.task_data)
        self.manager.current = 'detail'

class NewTaskScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root = BoxLayout(orientation='vertical')
        self.add_widget(self.root)
        self.edit_uid = None

    def load_form(self, default_tag='', edit_data=None):
        self.root.clear_widgets()
        self.edit_uid = edit_data[4] if edit_data else None

        header = BoxLayout(size_hint_y=None, height=55, padding=[5, 5])
        btn_back = Button(
            text='< Retour',
            size_hint_x=0.3,
            background_color=(0.2, 0.5, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        def go_back(x):
            self.manager.transition.direction = 'right'
            if self.edit_uid:
                self.manager.current = 'detail'
            else:
                self.manager.current = 'tags'
        btn_back.bind(on_press=go_back)
        header.add_widget(btn_back)
        header.add_widget(Label(
            text='Modifier' if edit_data else 'Nouvelle tache',
            bold=True, font_size=18,
            color=(0.2, 0.5, 0.9, 1)
        ))
        self.root.add_widget(header)

        layout = GridLayout(cols=1, spacing=12, size_hint_y=None, padding=[15, 10])
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(Label(
            text='Titre',
            size_hint_y=None, height=30,
            halign='left', valign='middle',
            text_size=(750, 30),
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        ))
        self.input_title = TextInput(
            hint_text='Titre de la tache...',
            text=edit_data[0] if edit_data else '',
            size_hint_y=None, height=50,
            multiline=False,
            font_size=15
        )
        layout.add_widget(self.input_title)

        layout.add_widget(Label(
            text='Tag (optionnel)',
            size_hint_y=None, height=30,
            halign='left', valign='middle',
            text_size=(750, 30),
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        ))
        current_tag = ''
        if edit_data:
            for tag, taches in PAR_TAG.items():
                for t in taches:
                    if t[4] == edit_data[4]:
                        current_tag = tag if tag != 'Sans tag' else ''
                        break
        self.input_tag = TextInput(
            hint_text='ex: TVX, IT, Home...',
            text=current_tag or default_tag,
            size_hint_y=None, height=50,
            multiline=False,
            font_size=15
        )
        layout.add_widget(self.input_tag)

        layout.add_widget(Label(
            text='Notes (optionnel)',
            size_hint_y=None, height=30,
            halign='left', valign='middle',
            text_size=(750, 30),
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        ))
        desc = edit_data[3] if edit_data and edit_data[3] != 'None' else ''
        self.input_desc = TextInput(
            hint_text='Notes...',
            text=desc,
            size_hint_y=None, height=120,
            multiline=True,
            font_size=15
        )
        layout.add_widget(self.input_desc)

        btn_save = Button(
            text='Enregistrer' if edit_data else 'Creer la tache',
            size_hint_y=None, height=55,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=16,
            bold=True
        )
        btn_save.bind(on_press=self.save_task)
        layout.add_widget(btn_save)

        scroll = ScrollView()
        scroll.add_widget(layout)
        self.root.add_widget(scroll)

    def save_task(self, btn):
        title = self.input_title.text.strip()
        if not title:
            return
        tag = self.input_tag.text.strip() or None
        desc = self.input_desc.text.strip()

        popup = loading_popup()
        def do_save(dt):
            global PAR_TAG
            if self.edit_uid:
                update_task(self.edit_uid, title, tag, desc)
            else:
                create_task(title, tag, desc)
            PAR_TAG = fetch_tasks()
            popup.dismiss()
            self.manager.get_screen('tags').build_ui()
            self.manager.transition.direction = 'right'
            self.manager.current = 'tags'
        Clock.schedule_once(do_save, 0.1)

class DetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root = BoxLayout(orientation='vertical')
        self.add_widget(self.root)
        self._cancel_event = None
        self._pending_uid = None

    def load_task(self, task_data):
        self.root.clear_widgets()
        self.task_data = task_data
        title_task, status, due_str, description, task_uid = task_data

        header = BoxLayout(size_hint_y=None, height=55, padding=[5, 5])
        btn_back = Button(
            text='< Retour',
            size_hint_x=0.25,
            background_color=(0.2, 0.5, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        def go_back(x):
            if self._cancel_event:
                self._cancel_event.cancel()
                self._cancel_event = None
                self._pending_uid = None
            self.manager.transition.direction = 'right'
            self.manager.current = 'tasks'
        btn_back.bind(on_press=go_back)

        btn_edit = Button(
            text='Modifier',
            size_hint_x=0.25,
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        def go_edit(x):
            self.manager.transition.direction = 'left'
            self.manager.get_screen('new').load_form(edit_data=self.task_data)
            self.manager.current = 'new'
        btn_edit.bind(on_press=go_edit)

        btn_delete = Button(
            text='Supprimer',
            size_hint_x=0.25,
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        def ask_delete(x):
            confirm_popup(
                f"Supprimer definitivement ?\n\n{title_task}",
                lambda: self.do_delete(task_uid)
            )
        btn_delete.bind(on_press=ask_delete)

        header.add_widget(btn_back)
        header.add_widget(Label(
            text='Detail',
            bold=True, font_size=16,
            color=(0.2, 0.5, 0.9, 1)
        ))
        header.add_widget(btn_edit)
        header.add_widget(btn_delete)
        self.root.add_widget(header)

        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=[15, 10])
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(Label(
            text=title_task,
            bold=True, font_size=20,
            size_hint_y=None, height=60,
            halign='left', valign='middle',
            text_size=(750, 60),
            color=(0.1, 0.1, 0.1, 1)
        ))

        icone = 'OK' if status == 'COMPLETED' else 'o'
        layout.add_widget(Label(
            text=f"Statut : {icone}  {status}",
            size_hint_y=None, height=40,
            halign='left', valign='middle',
            text_size=(750, 40),
            color=(0.3, 0.3, 0.3, 1),
            font_size=15
        ))

        if due_str:
            layout.add_widget(Label(
                text=f"Echeance : {due_str}",
                size_hint_y=None, height=40,
                halign='left', valign='middle',
                text_size=(750, 40),
                color=(0.2, 0.5, 0.9, 1),
                font_size=15
            ))

        if description and description != 'None':
            layout.add_widget(Label(
                text=f"Notes :\n{description}",
                size_hint_y=None, height=200,
                halign='left', valign='top',
                text_size=(750, 200),
                color=(0.3, 0.3, 0.3, 1),
                font_size=14
            ))

        if status != 'COMPLETED':
            self.btn_done = Button(
                text='Marquer comme faite',
                size_hint_y=None, height=55,
                background_color=(0.2, 0.7, 0.3, 1),
                color=(1, 1, 1, 1),
                font_size=16,
                bold=True
            )
            self.btn_done.task_uid = task_uid
            self.btn_done.task_title = title_task

            def ask_confirm(btn):
                confirm_popup(
                    f"Marquer comme faite ?\n\n{btn.task_title}",
                    lambda: self.start_countdown(btn.task_uid)
                )
            self.btn_done.bind(on_press=ask_confirm)
            layout.add_widget(self.btn_done)

            self.btn_cancel = Button(
                text='Annuler (3)',
                size_hint_y=None, height=55,
                background_color=(0.8, 0.4, 0.1, 1),
                color=(1, 1, 1, 1),
                font_size=16,
                bold=True,
                opacity=0,
                disabled=True
            )
            self.btn_cancel.bind(on_press=self.cancel_done)
            layout.add_widget(self.btn_cancel)

        scroll.add_widget(layout)
        self.root.add_widget(scroll)

    def do_delete(self, task_uid):
        popup = loading_popup()
        def _delete(dt):
            global PAR_TAG
            delete_task(task_uid)
            PAR_TAG = fetch_tasks()
            popup.dismiss()
            self.manager.get_screen('tags').build_ui()
            self.manager.transition.direction = 'right'
            self.manager.get_screen('tasks').load_tag(CURRENT_TAG)
            self.manager.current = 'tasks'
        Clock.schedule_once(_delete, 0.1)

    def start_countdown(self, task_uid):
        self._pending_uid = task_uid
        self._countdown = 3
        self.btn_done.disabled = True
        self.btn_done.opacity = 0
        self.btn_cancel.disabled = False
        self.btn_cancel.opacity = 1
        self.btn_cancel.text = f'Annuler ({self._countdown})'
        self._cancel_event = Clock.schedule_interval(self._tick, 1)

    def _tick(self, dt):
        self._countdown -= 1
        if self._countdown > 0:
            self.btn_cancel.text = f'Annuler ({self._countdown})'
        else:
            self._cancel_event.cancel()
            self._cancel_event = None
            self._execute_done()

    def cancel_done(self, *args):
        if self._cancel_event:
            self._cancel_event.cancel()
            self._cancel_event = None
        self._pending_uid = None
        self.btn_cancel.disabled = True
        self.btn_cancel.opacity = 0
        self.btn_done.disabled = False
        self.btn_done.opacity = 1
        self.btn_cancel.text = 'Annuler (3)'

    def _execute_done(self):
        success = mark_as_done(self._pending_uid)
        if success:
            global PAR_TAG
            PAR_TAG = fetch_tasks()
            self.manager.get_screen('tags').build_ui()
            self.manager.transition.direction = 'right'
            self.manager.get_screen('tasks').load_tag(CURRENT_TAG)
            self.manager.current = 'tasks'

class gtgDroidApp(App):
    title = 'gtgDroid'

    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(LoadingScreen(name='loading'))
        sm.add_widget(TagsScreen(name='tags'))
        sm.add_widget(TasksScreen(name='tasks'))
        sm.add_widget(DetailScreen(name='detail'))
        sm.add_widget(NewTaskScreen(name='new'))
        return sm

if __name__ == '__main__':
    gtgDroidApp().run()