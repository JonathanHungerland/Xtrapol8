import importlib
import types
import unittest
import warnings

from tests.helpers import (
    load_module_from_repo,
    patched_sys_modules,
    prepended_sys_path,
    temporary_package,
)


class PubsubCompatTests(unittest.TestCase):
    """Tests for the pubsub import shim used to bridge pypubsub and the Phenix fallback."""

    def test_prefers_standalone_pypubsub_when_available(self):
        """Covers the preferred import path so normal environments use standalone pypubsub first."""
        sentinel = object()
        pubsub_module = types.ModuleType("pubsub")
        pubsub_module.pub = sentinel

        with patched_sys_modules(
            modules={"pubsub": pubsub_module},
            clear=["wx", "wx.lib", "wx.lib.pubsub"],
        ):
            module = load_module_from_repo("pubsub_compat_standalone", "pubsub_compat.py")

        self.assertIs(module.pub, sentinel)

    def test_fallback_suppresses_wx_pubsub_deprecation_warning(self):
        """Covers the Phenix fallback path and verifies the known wx pubsub deprecation warning is suppressed."""
        files = {
            "wx/__init__.py": "",
            "wx/lib/__init__.py": "",
            "wx/lib/pubsub.py": (
                "import warnings\n"
                "warnings.warn(\n"
                "    'wx.lib.pubsub has been deprecated, please migrate your code to use pypubsub, available on PyPI.',\n"
                "    UserWarning,\n"
                ")\n"
                "pub = object()\n"
            ),
        }

        with temporary_package(files) as package_root:
            with prepended_sys_path(package_root):
                with patched_sys_modules(clear=["pubsub", "wx", "wx.lib", "wx.lib.pubsub"]):
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always")
                        module = load_module_from_repo("pubsub_compat_fallback", "pubsub_compat.py")
                    fallback_module = importlib.import_module("wx.lib.pubsub")

        self.assertIs(module.pub, fallback_module.pub)
        self.assertEqual(caught, [])


if __name__ == "__main__":
    unittest.main()
