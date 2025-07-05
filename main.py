from kivy.app import App
from kivy.uix.label import Label

class JoiApp(App):
    def build(self):
        return Label(text='Hola, Juan! Kivy App funcionando!')

if _name_ == '_main_':
    JoiApp().run()
