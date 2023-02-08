import ipywidgets as w
import torch
from ._sections import PDFImager

class PDFBrowser(w.VBox):
    def __init__(self):
        self.LOADED_MODELS = {}
        self.LOADED_IMAGES = []
        self.OUTPUT_IMAGES = {}

        self.pdfimager = PDFImager()

        w.VBox.__init__(self, children = [self.pdfimager], layout = w.Layout(width = "98%"))
