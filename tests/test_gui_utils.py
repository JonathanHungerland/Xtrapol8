import unittest

from tests.helpers import (
    FakeKeyEvent,
    load_module_from_repo,
    make_fake_wx_module,
    patched_sys_modules,
)


class CharValidatorTests(unittest.TestCase):
    """Unit tests for the lightweight character validator used by GUI text fields."""

    def load_module(self):
        fake_wx = make_fake_wx_module()
        with patched_sys_modules({"wx": fake_wx}):
            module = load_module_from_repo("gui_utils_under_test", "gui/utils.py")
        return module, fake_wx

    def test_clone_preserves_flag(self):
        """Covers Validator.Clone so wx can duplicate the validator without losing its filtering mode."""
        module, fake_wx = self.load_module()
        validator = module.CharValidator("no-alpha")
        clone = validator.Clone()

        self.assertIsInstance(clone, module.CharValidator)
        self.assertEqual(clone.flag, "no-alpha")
        self.assertEqual(len(validator.bound_events), 1)
        self.assertIs(validator.bound_events[0][0], fake_wx.EVT_CHAR)

    def test_no_alpha_rejects_letters(self):
        """Covers that no-alpha fields block alphabetic keyboard input."""
        module, _ = self.load_module()
        validator = module.CharValidator("no-alpha")
        event = FakeKeyEvent(ord("A"))

        validator.OnChar(event)

        self.assertFalse(event.skipped)

    def test_no_alpha_allows_digits(self):
        """Covers that no-alpha fields still pass numeric keyboard input through to wx."""
        module, _ = self.load_module()
        validator = module.CharValidator("no-alpha")
        event = FakeKeyEvent(ord("4"))

        validator.OnChar(event)

        self.assertTrue(event.skipped)

    def test_no_digit_rejects_digits(self):
        """Covers that no-digit fields block numeric keyboard input."""
        module, _ = self.load_module()
        validator = module.CharValidator("no-digit")
        event = FakeKeyEvent(ord("7"))

        validator.OnChar(event)

        self.assertFalse(event.skipped)

    def test_non_ascii_keys_are_passed_through(self):
        """Covers special keys and non-ASCII keycodes, which should not be filtered by the validator."""
        module, _ = self.load_module()
        validator = module.CharValidator("no-alpha")
        event = FakeKeyEvent(300)

        validator.OnChar(event)

        self.assertTrue(event.skipped)


if __name__ == "__main__":
    unittest.main()
