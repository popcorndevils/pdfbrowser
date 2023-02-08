import io
import ipywidgets as w
import fitz

class ImgSel(w.VBox):
    def __init__(self, img: fitz.Pixmap, element_index, *args, **kwargs):
        w.VBox.__init__(self, *args, **kwargs)
        self.layout.display = "flex"
        self.layout.align_items = "center"
        self.layout.flex_flow = "column"
        self.layout.justify_content = "flex-end"
        self.on_click = None
        self._img_data: fitz.Pixmap = img
        self._index = element_index
        self._btn = w.Button(layout = w.Layout(width = "100px"))
        self._name = w.Text(placeholder = "Image Name", layout = w.Layout(width = "100px"))

        self._btn.on_click(self.handle_click)
        self._name.on_submit(self.handle_click)

        _new_h = self._img_data.h
        _new_w = self._img_data.w

        if self._img_data.h > self._img_data.w and self._img_data.h > 100:
            _reduct = 100 / self._img_data.h
            _new_h = 100
            _new_w = self._img_data.w * _reduct
        elif self._img_data.w > self._img_data.h and self._img_data.w > 100:
            _reduct = 100 / self._img_data.w
            _new_w = 100
            _new_h = self._img_data.h * _reduct

        self._image = w.Image(layout = w.Layout(height = f"{_new_h}px", width = f"{_new_w}px"))
        self._image.value = self._img_data.tobytes()

        # default state
        self.selected = False
        self.children = (self._image, self._name, self._btn)

    @property
    def bytes(self):
        return io.BytesIO(self._img_data.tobytes())

    @property
    def index(self):
        return self._index

    @property
    def key(self):
        return f"{self._index[0]}_{self._index[1]}"

    @property
    def selected(self):
        return None

    @property
    def name(self):
        return self._name.value

    @property
    def list_name(self):
        _txt = f"Page {self.index[0] + 1}, Image {self.index[1] + 1}"
        _txt += f" ({self._name.value})" if self._name.value != "" else ""
        return _txt

    @property
    def path(self):
        _path = self.name if self.name != "" else f"pg{self.index[0] + 1}_i{self.index[1] + 1}"
        _path += ".png"
        return _path

    @selected.setter
    def selected(self, value: bool):
        if value:
            self.value = True
            self._name.disabled = True
            self._btn.description = "Selected"
            self._btn.button_style = "success"
        else:
            self.value = False
            self._name.disabled = False
            self._btn.description = "Extract"
            self._btn.button_style = "primary"

    def handle_click(self, _):
        self.selected = not self.value
        if self.on_click is not None:
            self.on_click(self)
