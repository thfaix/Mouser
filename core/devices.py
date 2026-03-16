"""
Device registry — maps Logitech product IDs to device configurations.

Supports MX Master 3S and MX Vertical.
"""

# ── Device type ─────────────────────────────────────────────────
DEVICE_TYPE_MOUSE = "mouse"

# ── Button definitions per device ───────────────────────────────

# MX Master 3S — all six programmable controls
MX_MASTER_3S_BUTTONS = {
    "middle":       "Middle button",
    "gesture":      "Gesture button",
    "xbutton1":     "Back button",
    "xbutton2":     "Forward button",
    "hscroll_left": "Horizontal scroll left",
    "hscroll_right":"Horizontal scroll right",
}

# MX Vertical — middle click + back/forward thumb buttons
# (no dedicated gesture button or horizontal-scroll tilt)
MX_VERTICAL_BUTTONS = {
    "middle":   "Middle button",
    "xbutton1": "Back button",
    "xbutton2": "Forward button",
}

# ── Device registry ─────────────────────────────────────────────
# Keys are Logitech product IDs (USB product_id field from hidapi).
DEVICES = {
    # MX Master 3S — Bluetooth
    0xB034: {
        "name":      "MX Master 3S",
        "type":      DEVICE_TYPE_MOUSE,
        "buttons":   MX_MASTER_3S_BUTTONS,
        "hid_cids":  [0x00C3],   # gesture button needs HID++ diversion
        "has_dpi":   True,
        "dpi_range": (200, 8000),
    },
    # MX Master 3S — Bolt receiver
    0xB037: {
        "name":      "MX Master 3S",
        "type":      DEVICE_TYPE_MOUSE,
        "buttons":   MX_MASTER_3S_BUTTONS,
        "hid_cids":  [0x00C3],
        "has_dpi":   True,
        "dpi_range": (200, 8000),
    },
    # MX Vertical — Bluetooth
    0xB020: {
        "name":      "MX Vertical",
        "type":      DEVICE_TYPE_MOUSE,
        "buttons":   MX_VERTICAL_BUTTONS,
        "hid_cids":  [],          # all buttons produce standard OS events
        "has_dpi":   True,
        "dpi_range": (400, 4000),
    },
    # MX Vertical — Bolt / Unifying receiver
    0xB013: {
        "name":      "MX Vertical",
        "type":      DEVICE_TYPE_MOUSE,
        "buttons":   MX_VERTICAL_BUTTONS,
        "hid_cids":  [],
        "has_dpi":   True,
        "dpi_range": (400, 4000),
    },
}

# Fallback used when the connected device PID is not in the registry
DEFAULT_DEVICE = {
    "name":      "MX Master 3S",
    "type":      DEVICE_TYPE_MOUSE,
    "buttons":   MX_MASTER_3S_BUTTONS,
    "hid_cids":  [0x00C3],
    "has_dpi":   True,
    "dpi_range": (200, 8000),
}


def get_device_config(pid: int) -> dict:
    """Return the device configuration dict for the given USB product ID.

    Falls back to *DEFAULT_DEVICE* when the PID is not in the registry.
    The returned dict is shared — do not mutate it.
    """
    return DEVICES.get(pid, DEFAULT_DEVICE)
