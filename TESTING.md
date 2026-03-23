# Testing Xtrapol8

Xtrapol8 now has a small, layered test suite aimed at the current porting work:

- A dependency-light base tier that runs under stock Python and protects the recent wxPython Phoenix fixes.
- An optional wx/iotbx smoke tier that instantiates the main GUI panels under a real GUI runtime.

## Run The Base Suite

From the repository root:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

This tier does not require Phenix, CCP4, `wx`, or `cctbx`. It focuses on:

- Phoenix regression guards in the GUI source tree.
- The pubsub compatibility shim.
- GUI helper behavior that can be exercised with a small fake `wx` module.

You can also run the same discovery entry point with:

```bash
python -m tests
```

## Run The Phenix GUI Smoke Tier

When testing the actual GUI runtime, use the Phenix interpreter:

```bash
phenix.python -m unittest discover -s tests -p 'test_*.py'
```

If `wx` and `iotbx` are importable and a GUI display is available, `tests/test_gui_wx_smoke.py` will also run. Those smoke tests instantiate:

- `gui.panelIO.TabIO`
- `gui.panelExtrapolation.TabExtrapolation`
- `gui.panelRefinement.TabRefinement`

This is the most direct automated check for the Phoenix sizer/layout regressions you have been fixing.

If those prerequisites are not present, the three smoke tests are skipped by design. The skip reason reports which prerequisite is missing:

- `wx is not installed`
- `iotbx is not installed`
- `no GUI display is available`

## Current Scope

The suite currently protects the GUI/Phoenix compatibility layer. It does not yet provide full workflow coverage for:

- `Fextr.py` end-to-end processing
- refinement handoff to Phenix or CCP4 tools
- numeric validation of map generation and occupancy estimation

Those next layers will need curated test data and explicit fixture handling for Phenix/CCP4-dependent jobs.
