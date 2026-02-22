from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from datetime import date
import state
from widgets import loading_popup


def is_actionable(task):
    # Exclure "Un jour"
    if task.priority == 9 or task.fuzzy == 'someday':
        return False
    # Exclure si DTSTART dans le futur
    if task.start_str:
        try:
            start_date = date(
                int(task.start_str[6:10]),
                int(task.start_str[3:5]),
                int(task.start_str[0:2])
            )
            if start_date > date.today():
                return False
        except Exception:
            pass
    return True


class TagsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation='vertical')

        # ── HEADER ────────────────────────────────────────────────
        header = BoxLayout(size_hint_y=None, height=55, padding=[5, 5])
        header.add_widget(Label(
            text='gtgDroid',
            bold=True, font_size=22,
            color=(0.2, 0.5, 0.9, 1)
        ))
        btn_refresh = Button(
            text='Rafraîchir',
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

        # ── BOUTONS DE VUE ────────────────────────────────────────
        view_bar = BoxLayout(size_hint_y=None, height=45, spacing=3, padding=[5, 3])

        def make_view_btn(text, view_name):
            is_active = state.CURRENT_VIEW == view_name
            btn = Button(
                text=text,
                background_color=(0.2, 0.5, 0.9, 1) if is_active else (0.7, 0.7, 0.7, 1),
                color=(1, 1, 1, 1),
                font_size=13,
                bold=is_active
            )
            def on_press(x, v=view_name):
                state.CURRENT_VIEW = v
                self.build_ui()
            btn.bind(on_press=on_press)
            return btn

        view_bar.add_widget(make_view_btn('Ouvertes', 'open'))
        view_bar.add_widget(make_view_btn('Actionnables', 'actionable'))
        view_bar.add_widget(make_view_btn('Fermées', 'closed'))
        view_bar.add_widget(make_view_btn('Abandonnées', 'dismissed'))
        root.add_widget(view_bar)

        # ── CALCUL DES TAGS SELON LA VUE ──────────────────────────
        par_tag_view = {}
        if state.CURRENT_VIEW == 'closed':
            source = state.PAR_TAG_CLOSED
        elif state.CURRENT_VIEW == 'dismissed':
            source = state.PAR_TAG_DISMISSED
        else:
            source = state.PAR_TAG

        for tag, taches in source.items():
            if state.CURRENT_VIEW == 'actionable':
                filtered = [t for t in taches if is_actionable(t)]
            else:
                filtered = taches
            if filtered:
                par_tag_view[tag] = filtered

        # ── LISTE DES TAGS ────────────────────────────────────────
        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=3, size_hint_y=None, padding=[10, 5])
        layout.bind(minimum_height=layout.setter('height'))

        for tag in sorted(par_tag_view.keys()):
            taches = par_tag_view[tag]
            nb = len(taches)

            # Compter les tâches avec enfants pour info visuelle
            nb_avec_enfants = sum(1 for t in taches if t.has_children)

            # Indicateur si le tag contient des tâches parentes
            indicateur = '  ▶' if nb_avec_enfants > 0 else ''

            btn = Button(
                text=f"  #{tag}  ({nb}){indicateur}",
                size_hint_y=None, height=55,
                halign='left',
                background_color=(1, 1, 1, 1),
                color=(0.2, 0.5, 0.9, 1),
                font_size=16,
                bold=True
            )
            btn.tag = tag
            btn.tag_tasks = taches
            btn.bind(on_press=self.go_to_tasks)
            layout.add_widget(btn)

        if not par_tag_view:
            layout.add_widget(Label(
                text='Aucune tâche dans cette vue.',
                size_hint_y=None, height=55,
                color=(0.5, 0.5, 0.5, 1),
                font_size=15
            ))

        scroll.add_widget(layout)
        root.add_widget(scroll)
        self.add_widget(root)

    def refresh(self, *args):
        popup = loading_popup()
        def do_refresh(dt):
            from caldav_api import fetch_all
            fetch_all()
            popup.dismiss()
            self.build_ui()
        Clock.schedule_once(do_refresh, 0.1)

    def go_to_tasks(self, btn):
        state.CURRENT_TAG = btn.tag
        self.manager.transition.direction = 'left'
        self.manager.get_screen('tasks').load_tag(btn.tag, btn.tag_tasks)
        self.manager.current = 'tasks'

    def go_to_new(self, btn):
        self.manager.transition.direction = 'left'
        self.manager.get_screen('new').load_form()
        self.manager.current = 'new'