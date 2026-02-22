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
        taches = sorted(taches, key=lambda x: x.due_str or 'zzz')

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

        # ── LISTE DES TÂCHES ──────────────────────────────────────
        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=2, size_hint_y=None, padding=[10, 5])
        layout.bind(minimum_height=layout.setter('height'))

        for task_data in taches:
            title_task = task_data.title
            status = task_data.status
            due_str = task_data.due_str
            task_uid = task_data.task_uid
            has_children = task_data.has_children
            priority = task_data.priority

            # Icône statut
            if status == 'COMPLETED':
                icone_statut = '✓'
            elif has_children:
                icone_statut = '▶'
            else:
                icone_statut = '○'

            # Couleur selon présence d'enfants
            if has_children:
                bg_color = (0.93, 0.95, 1.0, 1)
                txt_color = (0.15, 0.35, 0.75, 1)
            else:
                bg_color = (1, 1, 1, 1)
                txt_color = (0.1, 0.1, 0.1, 1)

            # Tags depuis le cache — zéro appel réseau
            tags_str = task_data.tags
            tags_autres = [t.strip() for t in tags_str.split(',')
                          if t.strip() and t.strip() != tag] if tags_str else []

            # Ligne principale : icône + titre + date
            date_str = f"   {due_str}" if due_str else ''
            ligne_titre = f"  {icone_statut}  {title_task}{date_str}"

            # Ligne secondaire : autres tags (sauf le tag courant)
            if tags_autres:
                ligne_tags = '  ' + '  '.join([f"@{t}" for t in tags_autres])
                hauteur = 65  # Plus haut pour afficher les deux lignes
                texte = f"{ligne_titre}\n{ligne_tags}"
                taille_tags = 12
            else:
                texte = ligne_titre
                hauteur = 50
                taille_tags = 0

            btn = Button(
                text=texte,
                size_hint_y=None, height=hauteur,
                halign='left',
                background_color=bg_color,
                color=txt_color,
                font_size=15
            )
            btn.task_data = task_data
            btn.bind(on_press=self.go_to_detail)
            layout.add_widget(btn)

        scroll.add_widget(layout)
        self.root.add_widget(scroll)

    def go_to_detail(self, btn):
        self.manager.transition.direction = 'left'
        self.manager.get_screen('detail').load_task(btn.task_data)
        self.manager.current = 'detail'