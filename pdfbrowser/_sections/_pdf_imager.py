import io
import pathlib

import fitz
import ipyvuetify as v
import ipywidgets as w
from ipyvuetify.extra import FileInput
from PIL import Image

from ._img_sel import ImgSel

class PDFImager(w.VBox):
    def __init__(self):
        self.IGNORE_CHG = False
        self.DOCUMENT_NAME = None
        self.DOCUMENT = None
        self.ELEMENTS = None
        self._PAGE_INDEX = 0
        self._ELEMENT_INDEX = 0
        self._ALL_IMAGES = {}
        self._SELECTIONS = {}

        self._upload_dialog = FileInput()
        self._upload_btn = w.Button(button_style = "success", description = "Upload PDF")
        self._export_selection = w.Button(button_style = "success", description = "Export Selection")
        self._btn_clear_selections = w.Button(description = "Clear", layout = w.Layout(width = "80px"))

        _btn_layout = w.Layout(width = "60px")
        _btn_layout_thin = w.Layout(width = "40px")

        self._btn_page_nav_first = w.Button(description = "<<<", layout = _btn_layout)
        self._btn_page_nav_prev = w.Button(description = "<", layout = _btn_layout_thin)
        self._page_nav = w.Dropdown(layout = w.Layout(width = "100px"))
        self._btn_page_nav_last = w.Button(description = ">>>", layout = _btn_layout)
        self._btn_page_nav_next = w.Button(description = ">", layout = _btn_layout_thin)

        self._btn_element_nav_first = w.Button(description = "<<<", layout = _btn_layout)
        self._btn_element_nav_prev = w.Button(description = "<", layout = _btn_layout_thin)
        self._element_nav = v.Html(tag='p', attributes={'title': 'a title'}, children=['-/-'])
        self._btn_element_nav_last = w.Button(description = ">>>", layout = _btn_layout)
        self._btn_element_nav_next = w.Button(description = ">", layout = _btn_layout_thin)

        self._sel_elements = w.Textarea(rows = 20, disabled = True)
        self._fld_prefix = w.Text(placeholder = "Optional Prefix", layout = w.Layout(width = "150px"))

        self._btn_page_nav_first.on_click(lambda _: self._set_page_index(0))
        self._btn_page_nav_prev.on_click(lambda _: self._set_page_index(self.PAGE_INDEX - 1))
        self._btn_page_nav_next.on_click(lambda _: self._set_page_index(self.PAGE_INDEX + 1))
        self._btn_page_nav_last.on_click(lambda _: self._set_page_index(len(self.DOCUMENT)))
        self._btn_clear_selections.on_click(self.handle_clear_selection)
        self._page_nav.observe(self.handle_page_select, "index")

        self._btn_element_nav_first.on_click(lambda _: self._set_element_index(0))
        self._btn_element_nav_prev.on_click(lambda _: self._set_element_index(
            self.ELEMENT_INDEX - 1))
        self._btn_element_nav_next.on_click(lambda _: self._set_element_index(
            self.ELEMENT_INDEX + 1))
        self._btn_element_nav_last.on_click(lambda _: self._set_element_index(
            len(self.ELEMENTS)))

        self._view_page = w.Image(layout = w.Layout(max_width = "300px", max_height = "500px"))
        self._view_image = w.Box(layout = w.Layout(max_height = "500px"))

        self._upload_btn.on_click(self.handle_upload)
        self._export_selection.on_click(self.handle_export)

        w.VBox.__init__(self, children = self.widgets)

    @property
    def widgets(self):
        return [
            self._upload_dialog,
            self._upload_btn,
            w.GridBox([
                w.HBox([
                    self._btn_page_nav_first,
                    self._btn_page_nav_prev,
                    self._page_nav,
                    self._btn_page_nav_next,
                    self._btn_page_nav_last,
                ]),
                w.HTML("<h2>Select Elements</h2>"),
                w.VBox([
                    w.HBox([
                        v.Html(tag='p', attributes={'title': 'a title'}, children=['Selected Elements']),
                        self._fld_prefix,
                    ]),
                    w.HBox([self._export_selection, self._btn_clear_selections])
                ]),               
                self._view_page,
                self._view_image,
                self._sel_elements], layout = w.Layout(grid_template_columns = "repeat(3, 1fr)"))
        ]

    @property
    def PAGE_INDEX(self):
        return self._PAGE_INDEX

    @PAGE_INDEX.setter
    def PAGE_INDEX(self, value):
        if self.DOCUMENT is not None and len(self.DOCUMENT) > 0:
            if value < 0:
                self._PAGE_INDEX = 0
            elif value >= len(self.DOCUMENT):
                self._PAGE_INDEX = len(self.DOCUMENT) - 1
            else:
                self._PAGE_INDEX = value

            _page = self.DOCUMENT[self._PAGE_INDEX]
            _page_im: fitz.Pixmap = _page.get_pixmap()
            self._view_page.value = _page_im.tobytes()
            self.IGNORE_CHG = True
            self._page_nav.index = self._PAGE_INDEX 
            self.IGNORE_CHG = False
            self.ELEMENTS = _page.get_images()
            self._view_image.children = [self._get_sub_img_grid(self.ELEMENTS)]

    # EVENT HANDLERS
    def handle_page_select(self, _):
        self.PAGE_INDEX = self._page_nav.index

    def handle_upload(self, _):
        _pdfs = self._upload_dialog.get_files()
        self.DOCUMENT_NAME = _pdfs[0]["name"]
        self.DOCUMENT = fitz.open("pdf", _pdfs[0]["file_obj"].read())
        self.IGNORE_CHG = True
        self._page_nav.options = [f"{i + 1}/{len(self.DOCUMENT)}" for i in range(len(self.DOCUMENT))]
        self._page_nav.index = 0
        self.IGNORE_CHG = False
        self.PAGE_INDEX = 0
        self._upload_dialog.clear()

    def handle_export(self, _):
        self._export_selection.disabled = True
        self._export_selection.description = "Extracting..."

        _export_path_parent = pathlib.Path("./export_images/")

        if not _export_path_parent.exists():
            _export_path_parent.mkdir()
        _export_path = pathlib.Path(f"{_export_path_parent}/{self.DOCUMENT_NAME}")
        if not _export_path.exists():
            _export_path.mkdir()

        for s in self._SELECTIONS.values():
            _path = str(_export_path.absolute()) + "/"
            _path += f"{self._fld_prefix.value}_" if self._fld_prefix.value != "" else ""
            _path += s.path
            Image.open(s.bytes).save(_path, format = "PNG")

        self._export_selection.disabled = False
        self._export_selection.description = "Export Selection"

    def handle_clear_selection(self, _):
        self._SELECTIONS = {}
        self._sel_elements.value = ""
        for btn in self._view_image.children[0].buttons:
            btn.value = False
            btn.description = "Extract"
            btn.button_style = "primary"

    def handle_element_selected(self, sel):
        if not sel.value:
            del self._SELECTIONS[sel.key]
        else:
            self._SELECTIONS[sel.key] = sel

        _selected = sorted(self._SELECTIONS.values(), key = lambda x: x.index)
        _names = [s.list_name for s in _selected]
        self._sel_elements.value = "\n".join(_names)

    # SPECIAL HELPERS
    def _set_page_index(self, val):
        self.PAGE_INDEX = val

    def _set_element_index(self, val):
        self.ELEMENT_INDEX = val

    def _get_element_data(self, element):
        _xref = element[0]
        _smask = element[1]

        _base_pix = fitz.Pixmap(self.DOCUMENT.extract_image(_xref)["image"])

        if _smask:
            _base_mask = fitz.Pixmap(self.DOCUMENT.extract_image(_smask)["image"])
            _base_image = fitz.Pixmap(_base_pix, _base_mask)
        else:
            _base_image = _base_pix

        return _base_image

    def _get_sub_img_grid(self, elements):
        # _output = w.GridBox(layout = w.Layout(grid_template_columns = "repeat(3, 1fr)", align_items = "flex-end", justify_items = "center"))
        _output = w.Box()
        _output.layout.display = "flex"
        _output.layout.flex_flow = "row wrap"
        # _output.layout.align_items = "center"

        _children = []

        for i, e in enumerate(elements):
            _ei = (self.PAGE_INDEX, i)
            _key = f"{_ei[0]}_{_ei[1]}"

            if _key not in self._ALL_IMAGES:
                _new_sel = ImgSel(self._get_element_data(e), _ei)
                _new_sel.on_click = self.handle_element_selected
                self._ALL_IMAGES[_key] = _new_sel

            _selector = self._ALL_IMAGES[_key]

            _children.append(_selector)

        _output.children = _children

        return _output
