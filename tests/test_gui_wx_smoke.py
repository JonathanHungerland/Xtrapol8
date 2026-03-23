import importlib.util
import os
import sys
import unittest


def has_module(name):
    return importlib.util.find_spec(name) is not None


HAS_WX = has_module("wx")
HAS_IOTBX = has_module("iotbx")
HAS_DISPLAY = not sys.platform.startswith("linux") or bool(os.environ.get("DISPLAY"))
CAN_OPEN_GUI = HAS_WX and HAS_IOTBX and HAS_DISPLAY

SKIP_REASONS = []
if not HAS_WX:
    SKIP_REASONS.append("wx is not installed")
if not HAS_IOTBX:
    SKIP_REASONS.append("iotbx is not installed")
if not HAS_DISPLAY:
    SKIP_REASONS.append("no GUI display is available")
SKIP_REASON = ", ".join(SKIP_REASONS) if SKIP_REASONS else ""


@unittest.skipUnless(
    CAN_OPEN_GUI,
    SKIP_REASON,
)
class WxGuiSmokeTests(unittest.TestCase):
    """Runtime smoke tests for panel construction under a real wx/iotbx environment."""

    @classmethod
    def setUpClass(cls):
        import wx

        cls.wx = wx
        cls.app = wx.App(False)

    @classmethod
    def tearDownClass(cls):
        cls.app.Destroy()

    def tearDown(self):
        if hasattr(self, "frame"):
            self.frame.Destroy()

    def test_tab_io_builds(self):
        """Covers that the IO panel can be instantiated without raising wx layout or import errors."""
        from gui.panelIO import TabIO

        self.frame = self.wx.Frame(None)
        panel = TabIO(self.frame)

        self.assertIsNotNone(panel.GetSizer())

    def test_tab_extrapolation_builds(self):
        """Covers that the extrapolation panel builds cleanly under the real Phoenix-era wx runtime."""
        from gui.panelExtrapolation import TabExtrapolation

        self.frame = self.wx.Frame(None)
        panel = TabExtrapolation(self.frame)

        self.assertIsNotNone(panel.GetSizer())

    def test_tab_refinement_builds(self):
        """Covers that the refinement panel builds without duplicate-control or sizer ownership failures."""
        from gui.panelRefinement import TabRefinement

        self.frame = self.wx.Frame(None)
        panel = TabRefinement(self.frame)

        self.assertIsNotNone(panel.GetSizer())


if __name__ == "__main__":
    unittest.main()
