from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup

def confirm_popup(message, on_confirm):
    content = BoxLayout(orientation='vertical', padding=10, spacing=10)
    content.add_widget(Label(text=message, halign='center'))
    buttons = BoxLayout(size_hint_y=None, height=45, spacing=10)
    popup = Popup(
        title='Confirmation',
        content=content,
        size_hint=(0.8, 0.35),
        auto_dismiss=False
    )
    btn_oui = Button(text='Oui', background_color=(0.8, 0.2, 0.2, 1), color=(1, 1, 1, 1))
    btn_non = Button(text='Non', background_color=(0.4, 0.4, 0.4, 1), color=(1, 1, 1, 1))
    def do_confirm(x):
        popup.dismiss()
        on_confirm()
    btn_oui.bind(on_press=do_confirm)
    btn_non.bind(on_press=popup.dismiss)
    buttons.add_widget(btn_oui)
    buttons.add_widget(btn_non)
    content.add_widget(buttons)
    popup.open()

def loading_popup():
    content = BoxLayout(orientation='vertical', padding=10)
    content.add_widget(Label(text='Actualisation en cours...', halign='center'))
    popup = Popup(
        title='',
        content=content,
        size_hint=(0.6, 0.2),
        auto_dismiss=False
    )
    popup.open()
    return popup