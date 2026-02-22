from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import state
from widgets import loading_popup


class TagsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build_ui(self):
        """Appelé par LoadingScreen après le fetch — redirige vers ActionScreen."""
        self.manager.get_screen('action').load_view(mode='open')
        self.manager.transition.direction = 'left'
        self.manager.current = 'action'

    def go_to_new(self, btn):
        self.manager.transition.direction = 'left'
        self.manager.get_screen('new').load_form()
        self.manager.current = 'new'

    def refresh(self, *args):
        popup = loading_popup()
        def do_refresh(dt):
            from caldav_api import fetch_all
            fetch_all()
            popup.dismiss()
            self.manager.get_screen('action').load_view(mode=state.CURRENT_VIEW)
            self.manager.transition.direction = 'left'
            self.manager.current = 'action'
        Clock.schedule_once(do_refresh, 0.1)