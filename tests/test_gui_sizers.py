import unittest

from tests.helpers import load_module_from_repo, make_fake_wx_module, patched_sys_modules


class DefaultHorizontalSizerTests(unittest.TestCase):
    """Behavioral tests for the small GUI helper sizer used throughout the IO panel."""

    def load_module(self):
        fake_wx = make_fake_wx_module()
        with patched_sys_modules({"wx": fake_wx}):
            module = load_module_from_repo("gui_sizers_under_test", "gui/Sizers.py")
        return module, fake_wx

    def test_single_line_sizer_builds_three_controls(self):
        """Covers the default single-line layout with label, text control, and browse button."""
        module, fake_wx = self.load_module()
        parent = object()
        sizer = module.DefaultHorizontalSizer(parent, "Output Directory :", "Browse")

        self.assertEqual(sizer.GetItemCount(), 3)
        self.assertEqual(sizer.StaticTxt.label, "Output Directory :")
        self.assertEqual(sizer.TextCtrl.style, 0)
        self.assertEqual(sizer.Btn.label, "Browse")
        self.assertEqual(sizer.items[0][2], fake_wx.ALL | fake_wx.ALIGN_CENTER_VERTICAL)

    def test_multiline_sizer_uses_readonly_multiline_text_control(self):
        """Covers the multiline variant so it stays read-only and uses the multiline wx style flags."""
        module, fake_wx = self.load_module()
        parent = object()
        sizer = module.DefaultHorizontalSizer(parent, "Extra Files :", "Browse", multiline=True)

        self.assertEqual(
            sizer.TextCtrl.style,
            fake_wx.TE_READONLY | fake_wx.TE_MULTILINE,
        )
        self.assertEqual(sizer.GetItemCount(), 3)


if __name__ == "__main__":
    unittest.main()
