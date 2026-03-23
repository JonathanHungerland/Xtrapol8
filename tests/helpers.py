import contextlib
import importlib.util
import sys
import tempfile
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module_from_repo(module_name, relative_path):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def patched_sys_modules(modules=None, clear=None):
    modules = modules or {}
    clear = clear or []
    touched = set(modules) | set(clear)
    original = {name: sys.modules.get(name) for name in touched}
    try:
        for name in clear:
            sys.modules.pop(name, None)
        sys.modules.update(modules)
        yield
    finally:
        for name in touched:
            sys.modules.pop(name, None)
        for name, value in original.items():
            if value is not None:
                sys.modules[name] = value


@contextlib.contextmanager
def prepended_sys_path(path):
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        try:
            sys.path.remove(str(path))
        except ValueError:
            pass


class FakeKeyEvent:
    def __init__(self, keycode):
        self._keycode = keycode
        self.skipped = False

    def GetKeyCode(self):
        return self._keycode

    def Skip(self):
        self.skipped = True


def make_fake_wx_module():
    wx = types.ModuleType("wx")

    class Validator:
        def __init__(self):
            self.bound_events = []

        def Bind(self, event, handler):
            self.bound_events.append((event, handler))

    class Widget:
        def __init__(self, parent, widget_id, label="", size=None, style=0, validator=None):
            self.parent = parent
            self.widget_id = widget_id
            self.label = label
            self.size = size
            self.style = style
            self.validator = validator

    class StaticText(Widget):
        pass

    class TextCtrl(Widget):
        pass

    class Button(Widget):
        pass

    class BoxSizer:
        def __init__(self, orient):
            self.orient = orient
            self.items = []

        def Add(self, item, proportion=0, flags=0, border=0):
            self.items.append((item, proportion, flags, border))

        def GetItemCount(self):
            return len(self.items)

    wx.Validator = Validator
    wx.StaticText = StaticText
    wx.TextCtrl = TextCtrl
    wx.Button = Button
    wx.BoxSizer = BoxSizer
    wx.EVT_CHAR = object()
    wx.HORIZONTAL = 1
    wx.ALL = 2
    wx.ALIGN_CENTER_VERTICAL = 4
    wx.ID_ANY = -1
    wx.TE_READONLY = 8
    wx.TE_MULTILINE = 16
    return wx


@contextlib.contextmanager
def temporary_package(package_files):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        for relative_path, content in package_files.items():
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        yield root

