from kivy.app import App
from kivy.uix.widget import Widget


class Prompt(Widget):
    pass


class PromptApp(App):
    def build(self):
        return Prompt()


def prompt(query):
    pass


if __name__=="__main__":
    PromptApp().run()