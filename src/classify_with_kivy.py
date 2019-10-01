from Dataset import Dataset
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.config import Config

Config.set('kivy', 'desktop', True)

exceptionValues = {
    "NO_INPUT": 1,
}

class ClassifyWindow(FloatLayout):
    pass


class CheckBoxBox(RelativeLayout):

    def getChecked(self):
        for child in self.children:
            # print(type(CheckBox()))
            if type(CheckBox()) == type(child):
                return child.active
        return False


class Bar(RelativeLayout):
    pass


class MenuButton(Button):
    pass


class ClassifyApp(App):

    def build(self):
        return ClassifyWindow()

    def beginClassify(self, uid, restart):
        res, ret = classify(uid, restart)
        if res == exceptionValues["NO_INPUT"]:
            popup = Popup(title="No Input",
                          content=Label(text=str(ret)),
                          size_hint=(None, None),
                          size=(300, 300))
            popup.open()


# Main function to put all images through our classification pipeline. Returns the dataset used during the pipeline.
def classify(uid, restart):
    try:
        dataset = Dataset(uid=uid, restart=restart)
    except Exception as e:
        return exceptionValues["NO_INPUT"], e
    dataset.detect_type_ones()
    dataset.predict_grids()
    dataset.get_stats()
    return dataset


if __name__ == '__main__':
    ClassifyApp().run()
# classify()