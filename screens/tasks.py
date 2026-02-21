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
        taches = sorted(taches, key=lambda x: x[2] or 'zzz')

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

        for title_task, status, due_str, start_str, description, task_uid, priority in taches:
            icone = 'OK' if status == 'COMPLETED' else 'o'
            date_str = f"   {due_str}" if due_str else ''
            btn = Button(
                text=f"  {icone}  {title_task}{date_str}",
                size_hint_y=None, height=50,
                halign='left',
                background_color=(1, 1, 1, 1),
                color=(0.1, 0.1, 0.1, 1),
                font_size=15
            )
            btn.task_data = (title_task, status, due_str, start_str, description, task_uid, priority)
            btn.bind(on_press=self.go_to_detail)
            layout.add_widget(btn)

        scroll.add_widget(layout)
        self.root.add_widget(scroll)

    def go_to_detail(self, btn):
        self.manager.transition.direction = 'left'
        self.manager.get_screen('detail').load_task(btn.task_data)
        self.manager.current = 'detail'