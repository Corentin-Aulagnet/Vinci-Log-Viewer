import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=6, height=4, dpi=100,_3D=False):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        if(_3D):self.axes = self.fig.add_subplot(projection='3d')
        else: self.axes = self.fig.add_subplot()
        self.twin = self.axes.twinx()
        self.twin.set_visible(False)
        super(MplCanvas, self).__init__(self.fig)