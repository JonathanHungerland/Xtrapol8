"""PubSub compatibility layer for Xtrapol8.

Prefer the standalone ``pypubsub`` package. Phenix 2.0 ships only the
deprecated ``wx.lib.pubsub`` namespace, so keep a narrow fallback for that
runtime and suppress the import-time deprecation warning.
"""

import warnings


try:
    from pubsub import pub
except ImportError:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"wx\.lib\.pubsub has been deprecated, please migrate your "
                    r"code to use pypubsub, available on PyPI\.",
        )
        from wx.lib.pubsub import pub
