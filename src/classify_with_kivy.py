from Dataset import Dataset
from LiraExceptions import InputEmptyError

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.config import Config
from kivy.core.image import Image as CoreImage
# from kivy.uix.image import Image as kiImage
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import cv2

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


class StartScreen(Screen):
    pass


class TypeOneScreen(Screen):
    pass


class Bar(RelativeLayout):
    pass


class MenuButton(Button):
    pass


class ClassifyApp(App):

    def __init__(self):
        App.__init__(self)
        self.manager = None
        # self.type_one_screen = None
        self.dataset = None
        self.img_resize_factor = 0.1

    def build(self):
        return ClassifyWindow()

    def beginClassify(self, uid, restart):
        self.manager = [i for i in self.root.children if i.name == 'screen_manager'][0]
        try:
            self.dataset = Dataset(uid=uid, restart=restart)
            self.dataset.detect_type_ones(kivy=True)
            self.moveToTypeOneDetectionEditor()
        except InputEmptyError as e:
            popup = Popup(title="No Input",
                          content=Label(text=str(e)),
                          size_hint=(None, None),
                          size=(300, 300))
            popup.open()
        # res, ret = classify(uid, restart)
        # if res == exceptionValues["NO_INPUT"]:
        # else

    def moveToTypeOneDetectionEditor(self):
        self.manager.current = 'type_one'
        type_one_screen = [i for i in self.manager.children if i.name == 'type_one'][0]
        type_one_image = type_one_screen.children[0].children[0].children[0]
        # print(self.dataset.imgs[self.dataset.progress["type_ones_image"]])
        texture = self.loadImage(self.dataset.imgs[self.dataset.progress["type_ones_image"]])
        type_one_image.texture = texture

    def loadImage(self, image):
        # takes an image from dataset and returns a format readable for Kivy
        cvImage = cv2.resize(image, (0, 0),
                              fx=self.img_resize_factor,
                              fy=self.img_resize_factor)
        cvImage = cv2.cvtColor(cvImage, cv2.COLOR_BGR2RGB)
        pilImage = Image.fromarray(cvImage)
        data = BytesIO()
        pilImage.save(data, format='png')
        data.seek(0)
        im = CoreImage(BytesIO(data.read()), ext='png')
        return im.texture




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