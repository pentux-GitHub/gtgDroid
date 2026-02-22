from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock


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
            text='Connexion à Nextcloud...',
            font_size=15,
            color=(0.4, 0.4, 0.4, 1)
        )
        layout.add_widget(self.status)
        self.add_widget(layout)

    def on_enter(self):
        Clock.schedule_once(self.load_data, 0.3)

    def load_data(self, dt):
        self.status.text = 'Chargement des tâches...'
        Clock.schedule_once(self._do_fetch, 0.1)

    def _do_fetch(self, dt):
        from caldav_api import fetch_all
        fetch_all()  # Un seul fetch — remplit PAR_TAG, PAR_TAG_CLOSED, PAR_TAG_DISMISSED, etc.
        self.manager.get_screen('action').load_view(mode='open')
        self.manager.transition.direction = 'left'
        self.manager.current = 'action'