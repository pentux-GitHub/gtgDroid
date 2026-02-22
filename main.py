from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window

from screens.loading import LoadingScreen
from screens.tags import TagsScreen
from screens.tasks import TasksScreen
from screens.detail import DetailScreen
from screens.new_task import NewTaskScreen
from screens.action import ActionScreen

Window.clearcolor = (0.95, 0.95, 0.95, 1)

class gtgDroidApp(App):
    title = 'gtgDroid'

    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(LoadingScreen(name='loading'))
        sm.add_widget(TagsScreen(name='tags'))
        sm.add_widget(TasksScreen(name='tasks'))
        sm.add_widget(DetailScreen(name='detail'))
        sm.add_widget(NewTaskScreen(name='new'))
        sm.add_widget(ActionScreen(name='action'))
        return sm

if __name__ == '__main__':
    gtgDroidApp().run()