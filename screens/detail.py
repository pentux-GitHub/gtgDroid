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

    def load_task(self, task_data):
        self.root.clear_widgets()
        self.task_data = task_data
        title_task, status, due_str, start_str, description, task_uid, priority = task_data

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

        if priority == 5:
            priorite_str = 'Bientot'
            priorite_color = (0.5, 0.4, 0.8, 1)
        elif priority == 9:
            priorite_str = 'Un jour'
            priorite_color = (0.5, 0.5, 0.5, 1)
        else:
            priorite_str = None

        if priorite_str:
            layout.add_widget(Label(
                text=f"Priorite : {priorite_str}",
                size_hint_y=None, height=40,
                halign='left', valign='middle',
                text_size=(750, 40),
                color=priorite_color,
                font_size=15
            ))

        if start_str:
            layout.add_widget(Label(
                text=f"Commence le : {start_str}",
                size_hint_y=None, height=40,
                halign='left', valign='middle',
                text_size=(750, 40),
                color=(0.5, 0.3, 0.8, 1),
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
            from caldav_api import delete_task, fetch_tasks
            delete_task(task_uid)
            state.PAR_TAG = fetch_tasks()
            popup.dismiss()
            self.manager.get_screen('tags').build_ui()
            self.manager.transition.direction = 'right'
            self.manager.get_screen('tasks').load_tag(state.CURRENT_TAG)
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
        from caldav_api import mark_as_done, fetch_tasks
        success = mark_as_done(self._pending_uid)
        if success:
            state.PAR_TAG = fetch_tasks()
            self.manager.get_screen('tags').build_ui()
            self.manager.transition.direction = 'right'
            self.manager.get_screen('tasks').load_tag(state.CURRENT_TAG)
            self.manager.current = 'tasks'