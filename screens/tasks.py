from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
import state


class TasksScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root = BoxLayout(orientation='vertical')
        self.add_widget(self.root)

    def load_tag(self, tag, taches=None):
        self.root.clear_widgets()

        if taches is None:
            taches = state.PAR_TAG.get(tag, [])

        # Séparer parents et tâches autonomes (sans parent)
        # Les tâches qui sont sous-tâches d'une autre ne s'affichent pas
        # au niveau racine — elles apparaissent indentées sous leur parent
        tous_les_uids = {t.task_uid for t in taches}
        subtasks_uids = set()
        for t in taches:
            if t.has_children:
                for sub in state.SUBTASKS_PAR_UID.get(t.task_uid, []):
                    subtasks_uids.add(sub.task_uid)

        # Tâches racines = pas sous-tâches d'une autre tâche du même tag
        racines = [t for t in taches if t.task_uid not in subtasks_uids]
        racines = sorted(racines, key=lambda x: x.due_str or 'zzz')

        # ── HEADER ────────────────────────────────────────────────
        header = BoxLayout(size_hint_y=None, height=55, padding=[5, 5])
        btn_back = Button(
            text='< Retour',
            size_hint_x=0.25,
            background_color=(0.2, 0.5, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        def go_back(x):
            self.manager.transition.direction = 'right'
            self.manager.current = 'tags'
        btn_back.bind(on_press=go_back)

        btn_new = Button(
            text='  +  ',
            size_hint_x=0.15,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=20,
            bold=True
        )
        def go_new(x):
            self.manager.transition.direction = 'left'
            self.manager.get_screen('new').load_form(default_tag=tag)
            self.manager.current = 'new'
        btn_new.bind(on_press=go_new)

        header.add_widget(btn_back)
        header.add_widget(Label(
            text=f"#{tag}",
            bold=True, font_size=18,
            color=(0.2, 0.5, 0.9, 1)
        ))
        header.add_widget(btn_new)
        self.root.add_widget(header)

        # ── LISTE ARBORESCENTE ────────────────────────────────────
        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=2, size_hint_y=None, padding=[10, 5])
        layout.bind(minimum_height=layout.setter('height'))

        for task_data in racines:
            self._add_task_row(layout, task_data, tag, indent=0)

            # Sous-tâches indentées si la tâche est parente
            if task_data.has_children:
                subtasks = state.SUBTASKS_PAR_UID.get(task_data.task_uid, [])
                for sub in subtasks:
                    self._add_task_row(layout, sub, tag, indent=1)

        scroll.add_widget(layout)
        self.root.add_widget(scroll)

    def _add_task_row(self, layout, task_data, tag, indent=0):
        status = task_data.status
        due_str = task_data.due_str
        has_children = task_data.has_children

        # Icône statut
        if status == 'COMPLETED':
            icone_statut = '✓'
        elif status == 'CANCELLED':
            icone_statut = '✕'
        elif has_children:
            icone_statut = '▶'
        else:
            icone_statut = '○'

        # Couleurs
        if indent > 0:
            # Sous-tâche
            if status == 'COMPLETED':
                bg_color = (0.94, 0.97, 0.94, 1)
                txt_color = (0.4, 0.6, 0.4, 1)
            else:
                bg_color = (0.97, 0.97, 1.0, 1)
                txt_color = (0.2, 0.2, 0.5, 1)
        elif has_children:
            bg_color = (0.93, 0.95, 1.0, 1)
            txt_color = (0.15, 0.35, 0.75, 1)
        else:
            bg_color = (1, 1, 1, 1)
            txt_color = (0.1, 0.1, 0.1, 1)

        # Tags autres que le courant
        tags_str = task_data.tags
        tags_autres = [t.strip() for t in tags_str.split(',')
                      if t.strip() and t.strip() != tag] if tags_str else []

        # Indentation visuelle
        prefix = '      ' if indent > 0 else '  '

        date_str = f"   {due_str}" if due_str else ''
        ligne_titre = f"{prefix}{icone_statut}  {task_data.title}{date_str}"

        if tags_autres:
            ligne_tags = f"{prefix}  " + '  '.join([f"@{t}" for t in tags_autres])
            texte = f"{ligne_titre}\n{ligne_tags}"
            hauteur = 65
        else:
            texte = ligne_titre
            hauteur = 50 if indent == 0 else 44

        btn = Button(
            text=texte,
            size_hint_y=None, height=hauteur,
            halign='left',
            background_color=bg_color,
            color=txt_color,
            font_size=15 if indent == 0 else 13
        )
        btn.task_data = task_data
        btn.bind(on_press=self.go_to_detail)
        layout.add_widget(btn)

    def go_to_detail(self, btn):
        self.manager.transition.direction = 'left'
        self.manager.get_screen('detail').load_task(btn.task_data, from_screen='tasks')
        self.manager.current = 'detail'