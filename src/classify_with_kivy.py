from Dataset import Dataset
from kivy.app import App
from kivy.uix.widget import Widget

Config.set('kivy', 'desktop', True)

class ClassifyWindow(Widget):
    pass


class ClassifyApp(App):
    def build(self):
        return ClassifyWindow


#Main function to put all images through our classification pipeline. Returns the dataset used during the pipeline.
def classify(uid, restart):
    dataset = Dataset(uid=uid, restart=restart)
    dataset.detect_type_ones()
    dataset.predict_grids()
    dataset.get_stats()
    return dataset

if __name__ == '__main__':
    ClassifyApp().run()
# classify()