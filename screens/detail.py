from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import state
from widgets import confirm_popup, loading_popup


class DetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root = BoxLayout(orientation='vertical')
        self.add_widget(self.root)
        self._cancel_event = None
        self._pending_uid = None
        self._from_parent_data = None

    def load_task(self, task_data, from_parent_data=None):
        self.root.clear_widgets()
        self.task_data = task_data
        self._from_parent_data = from_parent_data

        title_task, status, due_str, start_str, description, task_uid, priority, has_children = task_data

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
            if self._cancel_event:
                self._cancel_event.cancel()
                self._cancel_event = None
                self._pending_uid = None
            self.manager.transition.direction = 'right'
            if self._from_parent_data is not None:
                self.load_task(self._from_parent_data)
            else:
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
                f"Supprimer définitivement ?\n\n{title_task}",
                lambda: self.do_delete(task_uid)
            )
        btn_delete.bind(on_press=ask_delete)

        header.add_widget(btn_back)
        header.add_widget(Label(
            text='Détail',
            bold=True, font_size=16,
            color=(0.2, 0.5, 0.9, 1)
        ))
        header.add_widget(btn_edit)
        header.add_widget(btn_delete)
        self.root.add_widget(header)

        # ── CORPS SCROLLABLE ──────────────────────────────────────
        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=[15, 10])
        layout.bind(minimum_height=layout.setter('height'))

        # Titre avec indice visuel
        titre_affiche = f"▶  {title_task}" if has_children else title_task
        layout.add_widget(Label(
            text=titre_affiche,
            bold=True, font_size=20,
            size_hint_y=None, height=60,
            halign='left', valign='middle',
            text_size=(750, 60),
            color=(0.2, 0.5, 0.9, 1) if has_children else (0.1, 0.1, 0.1, 1)
        ))

        # Tags — lecture depuis le cache, zéro appel réseau
        tags_str = state.TAGS_PAR_UID.get(task_uid, '')
        if tags_str:
            tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]
            tags_affiche = '  '.join([f"@{t}" for t in tags_list])
            layout.add_widget(Label(
                text=f"  {tags_affiche}",
                size_hint_y=None, height=32,
                halign='left', valign='middle',
                text_size=(750, 32),
                color=(0.8, 0.6, 0.0, 1),
                font_size=14,
                bold=True
            ))

        # Statut
        icone = '✓' if status == 'COMPLETED' else '○'
        layout.add_widget(Label(
            text=f"Statut : {icone}  {status}",
            size_hint_y=None, height=40,
            halign='left', valign='middle',
            text_size=(750, 40),
            color=(0.3, 0.3, 0.3, 1),
            font_size=15
        ))

        # Priorité fuzzy
        if priority == 5:
            priorite_str = 'Bientôt'
            priorite_color = (0.5, 0.4, 0.8, 1)
        elif priority == 9:
            priorite_str = 'Un jour'
            priorite_color = (0.5, 0.5, 0.5, 1)
        else:
            priorite_str = None

        if priorite_str:
            layout.add_widget(Label(
                text=f"Priorité : {priorite_str}",
                size_hint_y=None, height=40,
                halign='left', valign='middle',
                text_size=(750, 40),
                color=priorite_color,
                font_size=15
            ))

        # Date de début
        if start_str:
            layout.add_widget(Label(
                text=f"Commence le : {start_str}",
                size_hint_y=None, height=40,
                halign='left', valign='middle',
                text_size=(750, 40),
                color=(0.5, 0.3, 0.8, 1),
                font_size=15
            ))

        # Échéance
        if due_str:
            layout.add_widget(Label(
                text=f"Échéance : {due_str}",
                size_hint_y=None, height=40,
                halign='left', valign='middle',
                text_size=(750, 40),
                color=(0.2, 0.5, 0.9, 1),
                font_size=15
            ))

        # Notes
        if description and description != 'None':
            layout.add_widget(Label(
                text=f"Notes :\n{description}",
                size_hint_y=None, height=200,
                halign='left', valign='top',
                text_size=(750, 200),
                color=(0.3, 0.3, 0.3, 1),
                font_size=14
            ))

        # ── BOUTON AJOUTER SOUS-TÂCHE ─────────────────────────────
        btn_add_sub = Button(
            text='+ Ajouter une sous-tâche',
            size_hint_y=None, height=45,
            background_color=(0.3, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        def go_add_subtask(x):
            self.manager.transition.direction = 'left'
            self.manager.get_screen('new').load_form(parent_uid=task_uid)
            self.manager.current = 'new'
        btn_add_sub.bind(on_press=go_add_subtask)
        layout.add_widget(btn_add_sub)

        # ── SECTION SOUS-TÂCHES — depuis le cache ─────────────────
        if has_children:
            layout.add_widget(Label(
                text='── Sous-tâches ──────────────────────',
                size_hint_y=None, height=35,
                halign='left', valign='middle',
                text_size=(750, 35),
                color=(0.4, 0.4, 0.4, 1),
                font_size=13
            ))

            self.subtasks_layout = GridLayout(
                cols=1, spacing=2, size_hint_y=None
            )
            self.subtasks_layout.bind(minimum_height=self.subtasks_layout.setter('height'))
            layout.add_widget(self.subtasks_layout)

            layout.add_widget(Label(
                text='─────────────────────────────────────',
                size_hint_y=None, height=20,
                halign='left', valign='middle',
                text_size=(750, 20),
                color=(0.4, 0.4, 0.4, 1),
                font_size=13
            ))

            # Charger depuis le cache — instantané
            self._load_subtasks(task_uid)

        # ── BOUTONS D'ACTION ──────────────────────────────────────
        if status != 'COMPLETED':

            self.btn_done = Button(
                text='✓  Marquer comme faite',
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

            btn_reset = Button(
                text='↺  Réinitialiser → "Un jour"',
                size_hint_y=None, height=55,
                background_color=(0.4, 0.5, 0.7, 1),
                color=(1, 1, 1, 1),
                font_size=16,
                bold=True
            )
            def ask_reset(x):
                msg = f"Archiver et recréer cette tâche ?\n\n{title_task}\n\nLes sous-tâches cochées seront\narchivées et recréées à zéro." if has_children else f"Archiver et recréer cette tâche ?\n\n{title_task}"
                confirm_popup(msg, lambda: self.do_reset(task_uid))
            btn_reset.bind(on_press=ask_reset)
            layout.add_widget(btn_reset)

        scroll.add_widget(layout)
        self.root.add_widget(scroll)

    def _load_subtasks(self, parent_uid):
        """Charge les sous-tâches depuis le cache state — instantané."""
        from caldav_api import fetch_subtasks
        subtasks = fetch_subtasks(parent_uid)
        self.subtasks_layout.clear_widgets()

        if not subtasks:
            self.subtasks_layout.add_widget(Label(
                text='  Aucune sous-tâche.',
                size_hint_y=None, height=40,
                halign='left', valign='middle',
                text_size=(750, 40),
                color=(0.6, 0.6, 0.6, 1),
                font_size=14
            ))
            return

        for sub_data in subtasks:
            self._add_subtask_row(sub_data)

    def _add_subtask_row(self, sub_data):
        """Ajoute une ligne de sous-tâche avec case à cocher et bouton détail."""
        sub_title, sub_status, sub_due, sub_start, sub_desc, sub_uid, sub_priority, sub_has_children = sub_data

        row = BoxLayout(size_hint_y=None, height=50, spacing=5)

        is_done = sub_status == 'COMPLETED'
        btn_check = Button(
            text='✓' if is_done else '○',
            size_hint_x=None, width=50,
            background_color=(0.2, 0.7, 0.3, 1) if is_done else (0.85, 0.85, 0.85, 1),
            color=(1, 1, 1, 1) if is_done else (0.3, 0.3, 0.3, 1),
            font_size=18,
            bold=True,
            disabled=is_done
        )
        if not is_done:
            btn_check.sub_uid = sub_uid
            btn_check.sub_title = sub_title
            btn_check.bind(on_press=self._toggle_subtask)

        titre_affiche = f"▶ {sub_title}" if sub_has_children else sub_title
        couleur_titre = (0.5, 0.5, 0.5, 1) if is_done else (0.1, 0.1, 0.1, 1)

        lbl_title = Label(
            text=titre_affiche,
            halign='left', valign='middle',
            text_size=(600, 50),
            color=couleur_titre,
            font_size=15
        )

        btn_detail = Button(
            text='>',
            size_hint_x=None, width=45,
            background_color=(0.7, 0.7, 0.7, 1),
            color=(1, 1, 1, 1),
            font_size=16,
            bold=True
        )
        btn_detail.sub_data = sub_data
        btn_detail.bind(on_press=self._go_to_subtask_detail)

        row.add_widget(btn_check)
        row.add_widget(lbl_title)
        row.add_widget(btn_detail)
        self.subtasks_layout.add_widget(row)

    def _toggle_subtask(self, btn):
        confirm_popup(
            f"Marquer comme faite ?\n\n{btn.sub_title}",
            lambda: self._do_check_subtask(btn.sub_uid)
        )

    def _do_check_subtask(self, sub_uid):
        popup = loading_popup()
        def _execute(dt):
            from caldav_api import mark_as_done, fetch_tasks
            mark_as_done(sub_uid)
            fetch_tasks()  # Rafraîchit le cache complet
            popup.dismiss()
            self._load_subtasks(self.task_data[5])
        Clock.schedule_once(_execute, 0.1)

    def _go_to_subtask_detail(self, btn):
        """Navigue vers le détail d'une sous-tâche — mémorise le parent pour le retour."""
        self.manager.transition.direction = 'left'
        self.load_task(btn.sub_data, from_parent_data=self.task_data)
        self.manager.current = 'detail'

    def do_delete(self, task_uid):
        popup = loading_popup()
        def _delete(dt):
            from caldav_api import delete_task, fetch_tasks
            delete_task(task_uid)
            fetch_tasks()
            popup.dismiss()
            self.manager.get_screen('tags').build_ui()
            self.manager.transition.direction = 'right'
            self.manager.get_screen('tasks').load_tag(state.CURRENT_TAG)
            self.manager.current = 'tasks'
        Clock.schedule_once(_delete, 0.1)

    def do_reset(self, task_uid):
        popup = loading_popup()
        def _execute(dt):
            from caldav_api import reset_and_clone_task, fetch_tasks
            reset_and_clone_task(task_uid)
            fetch_tasks()
            popup.dismiss()
            self.manager.get_screen('tags').build_ui()
            self.manager.transition.direction = 'right'
            self.manager.get_screen('tasks').load_tag(state.CURRENT_TAG)
            self.manager.current = 'tasks'
        Clock.schedule_once(_execute, 0.1)

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
        from caldav_api import mark_as_done, fetch_tasks
        success = mark_as_done(self._pending_uid)
        if success:
            fetch_tasks()
            self.manager.get_screen('tags').build_ui()
            self.manager.transition.direction = 'right'
            self.manager.get_screen('tasks').load_tag(state.CURRENT_TAG)
            self.manager.current = 'tasks'