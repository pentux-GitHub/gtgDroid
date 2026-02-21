from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from datetime import date, timedelta
import state
from widgets import loading_popup

PRIORITY_BIENTOT = 5
PRIORITY_UN_JOUR = 9

def today_str():
    return date.today().strftime('%d/%m/%Y')


class NewTaskScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root = BoxLayout(orientation='vertical')
        self.add_widget(self.root)
        self.edit_uid = None

    def load_form(self, default_tag='', edit_data=None):
        self.root.clear_widgets()
        self.edit_uid = edit_data[5] if edit_data else None

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

        # Titre
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

        # Tag
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
            for tag, taches in state.PAR_TAG.items():
                for t in taches:
                    if t[5] == edit_data[5]:
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

        # Commence le
        layout.add_widget(Label(
            text='Commence le (optionnel)',
            size_hint_y=None, height=30,
            halign='left', valign='middle',
            text_size=(750, 30),
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        ))
        self.input_start = TextInput(
            hint_text='JJ/MM/AAAA',
            text=edit_data[3] if edit_data else '',
            size_hint_y=None, height=50,
            multiline=False,
            font_size=15
        )
        layout.add_widget(self.input_start)

        btn_start_today = Button(
            text="Aujourd'hui",
            size_hint_y=None, height=45,
            background_color=(0.3, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        def set_start_today(x):
            self.input_start.text = today_str()
        btn_start_today.bind(on_press=set_start_today)
        layout.add_widget(btn_start_today)

        # Echéance
        layout.add_widget(Label(
            text='Echeance (optionnel)',
            size_hint_y=None, height=30,
            halign='left', valign='middle',
            text_size=(750, 30),
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        ))
        self.input_due = TextInput(
            hint_text='JJ/MM/AAAA',
            text=edit_data[2] if edit_data else '',
            size_hint_y=None, height=50,
            multiline=False,
            font_size=15
        )
        layout.add_widget(self.input_due)

        btn_due_today = Button(
            text="Aujourd'hui",
            size_hint_y=None, height=45,
            background_color=(0.3, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        def set_due_today(x):
            self.input_due.text = today_str()
        btn_due_today.bind(on_press=set_due_today)
        layout.add_widget(btn_due_today)

        # Priorité fuzzy
        layout.add_widget(Label(
            text='Quand ? (optionnel)',
            size_hint_y=None, height=30,
            halign='left', valign='middle',
            text_size=(750, 30),
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        ))

        # Priorité courante si édition
        current_priority = edit_data[6] if edit_data else 0
        self._priority = current_priority

        btns_priority = BoxLayout(size_hint_y=None, height=50, spacing=5)

        self.btn_bientot = Button(
            text='Bientot',
            background_color=(0.5, 0.4, 0.8, 1) if current_priority == PRIORITY_BIENTOT else (0.8, 0.8, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        self.btn_un_jour = Button(
            text='Un jour',
            background_color=(0.4, 0.4, 0.4, 1) if current_priority == PRIORITY_UN_JOUR else (0.8, 0.8, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        self.btn_aucune = Button(
            text='Maintenant',
            background_color=(0.3, 0.7, 0.4, 1) if current_priority == 0 else (0.8, 0.8, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )

        def set_bientot(x):
            self._priority = PRIORITY_BIENTOT
            self.btn_bientot.background_color = (0.5, 0.4, 0.8, 1)
            self.btn_un_jour.background_color = (0.8, 0.8, 0.8, 1)
            self.btn_aucune.background_color = (0.8, 0.8, 0.8, 1)

        def set_un_jour(x):
            self._priority = PRIORITY_UN_JOUR
            self.btn_bientot.background_color = (0.8, 0.8, 0.8, 1)
            self.btn_un_jour.background_color = (0.4, 0.4, 0.4, 1)
            self.btn_aucune.background_color = (0.8, 0.8, 0.8, 1)

        def set_aucune(x):
            self._priority = 0
            self.btn_bientot.background_color = (0.8, 0.8, 0.8, 1)
            self.btn_un_jour.background_color = (0.8, 0.8, 0.8, 1)
            self.btn_aucune.background_color = (0.3, 0.7, 0.4, 1)

        self.btn_bientot.bind(on_press=set_bientot)
        self.btn_un_jour.bind(on_press=set_un_jour)
        self.btn_aucune.bind(on_press=set_aucune)

        btns_priority.add_widget(self.btn_bientot)
        btns_priority.add_widget(self.btn_un_jour)
        btns_priority.add_widget(self.btn_aucune)
        layout.add_widget(btns_priority)

        # Notes
        layout.add_widget(Label(
            text='Notes (optionnel)',
            size_hint_y=None, height=30,
            halign='left', valign='middle',
            text_size=(750, 30),
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        ))
        desc = edit_data[4] if edit_data and edit_data[4] != 'None' else ''
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
        start = self.input_start.text.strip() or None
        due = self.input_due.text.strip() or None
        desc = self.input_desc.text.strip()
        priority = self._priority

        popup = loading_popup()
        def do_save(dt):
            from caldav_api import create_task, update_task, fetch_tasks
            if self.edit_uid:
                update_task(self.edit_uid, title, tag, start, due, desc, priority)
            else:
                create_task(title, tag, start, due, desc, priority)
            state.PAR_TAG = fetch_tasks()
            popup.dismiss()
            self.manager.get_screen('tags').build_ui()
            self.manager.transition.direction = 'right'
            self.manager.current = 'tags'
        Clock.schedule_once(do_save, 0.1)