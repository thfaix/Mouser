"""
keyboard_hook.py — Low-level keyboard hook for MX Keys F-key remapping.

Intercepts F1–F12 key presses system-wide so they can be remapped to any
action defined in key_simulator.ACTIONS.

Supported platforms: Windows (WH_KEYBOARD_LL) and macOS (CGEventTap).
"""

import sys
import threading
import time


# ==================================================================
# Shared: KeyboardEvent (platform-neutral)
# ==================================================================

class KeyboardEvent:
    """Represents a captured keyboard event."""

    def __init__(self, event_type):
        self.event_type = event_type
        self.timestamp  = time.time()


# ==================================================================
# Windows implementation
# ==================================================================

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes as wintypes
    from ctypes import CFUNCTYPE, Structure, c_int, windll

    WH_KEYBOARD_LL = 13
    WM_KEYDOWN     = 0x0100
    WM_SYSKEYDOWN  = 0x0104
    WM_QUIT        = 0x0012
    HC_ACTION      = 0

    # Virtual-key codes for F1–F12
    VK_F1  = 0x70
    VK_F2  = 0x71
    VK_F3  = 0x72
    VK_F4  = 0x73
    VK_F5  = 0x74
    VK_F6  = 0x75
    VK_F7  = 0x76
    VK_F8  = 0x77
    VK_F9  = 0x78
    VK_F10 = 0x79
    VK_F11 = 0x7A
    VK_F12 = 0x7B

    # Flag set by our own SendInput injections — skip those
    LLKHF_INJECTED = 0x00000010

    VK_TO_EVENT = {
        VK_F1:  "f1",
        VK_F2:  "f2",
        VK_F3:  "f3",
        VK_F4:  "f4",
        VK_F5:  "f5",
        VK_F6:  "f6",
        VK_F7:  "f7",
        VK_F8:  "f8",
        VK_F9:  "f9",
        VK_F10: "f10",
        VK_F11: "f11",
        VK_F12: "f12",
    }

    class KBDLLHOOKSTRUCT(Structure):
        _fields_ = [
            ("vkCode",      wintypes.DWORD),
            ("scanCode",    wintypes.DWORD),
            ("flags",       wintypes.DWORD),
            ("time",        wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    HOOKPROC = CFUNCTYPE(ctypes.c_long, c_int,
                         wintypes.WPARAM,
                         ctypes.POINTER(KBDLLHOOKSTRUCT))

    SetWindowsHookExW  = windll.user32.SetWindowsHookExW
    SetWindowsHookExW.restype  = wintypes.HHOOK
    SetWindowsHookExW.argtypes = [c_int, HOOKPROC,
                                   wintypes.HINSTANCE, wintypes.DWORD]

    CallNextHookEx = windll.user32.CallNextHookEx
    CallNextHookEx.restype  = ctypes.c_long
    CallNextHookEx.argtypes = [wintypes.HHOOK, c_int,
                                wintypes.WPARAM,
                                ctypes.POINTER(KBDLLHOOKSTRUCT)]

    UnhookWindowsHookEx = windll.user32.UnhookWindowsHookEx
    UnhookWindowsHookEx.restype  = wintypes.BOOL
    UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]

    GetModuleHandleW = windll.kernel32.GetModuleHandleW
    GetModuleHandleW.restype  = wintypes.HMODULE
    GetModuleHandleW.argtypes = [wintypes.LPCWSTR]

    GetMessageW        = windll.user32.GetMessageW
    PostThreadMessageW = windll.user32.PostThreadMessageW

    class KeyboardHook:
        """
        Installs a low-level keyboard hook on Windows to intercept
        F1–F12 key presses and remap them to custom actions.
        """

        def __init__(self):
            self._hook         = None
            self._hook_thread  = None
            self._thread_id    = None
            self._running      = False
            self._callbacks    = {}
            self._blocked_events = set()
            self._hook_proc    = None

        # ── binding API ───────────────────────────────────────

        def register(self, event_type, callback):
            self._callbacks.setdefault(event_type, []).append(callback)

        def block(self, event_type):
            self._blocked_events.add(event_type)

        def unblock(self, event_type):
            self._blocked_events.discard(event_type)

        def reset_bindings(self):
            self._callbacks.clear()
            self._blocked_events.clear()

        # ── dispatch ──────────────────────────────────────────

        def _dispatch(self, event):
            for cb in self._callbacks.get(event.event_type, []):
                try:
                    cb(event)
                except Exception as exc:
                    print(f"[KeyboardHook] callback error: {exc}")

        # ── hook procedure ────────────────────────────────────

        def _low_level_handler(self, nCode, wParam, lParam):
            if nCode == HC_ACTION and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                data = lParam.contents
                # Skip injected events (our own SendInput)
                if not (data.flags & LLKHF_INJECTED):
                    evt_type = VK_TO_EVENT.get(data.vkCode)
                    if evt_type and evt_type in self._blocked_events:
                        self._dispatch(KeyboardEvent(evt_type))
                        return 1   # suppress the original key press
            return CallNextHookEx(self._hook, nCode, wParam, lParam)

        # ── lifecycle ─────────────────────────────────────────

        def _run_hook(self):
            self._thread_id = windll.kernel32.GetCurrentThreadId()
            self._hook_proc = HOOKPROC(self._low_level_handler)
            self._hook = SetWindowsHookExW(
                WH_KEYBOARD_LL, self._hook_proc,
                GetModuleHandleW(None), 0)
            if not self._hook:
                print("[KeyboardHook] Failed to install hook!")
                return
            print("[KeyboardHook] Hook installed successfully")
            self._running = True

            msg = wintypes.MSG()
            while self._running:
                result = GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result == 0 or result == -1:
                    break

            if self._hook:
                UnhookWindowsHookEx(self._hook)
                self._hook = None
            print("[KeyboardHook] Hook removed")

        def start(self):
            if self._hook_thread and self._hook_thread.is_alive():
                return
            self._hook_thread = threading.Thread(
                target=self._run_hook, daemon=True, name="KeyboardHook")
            self._hook_thread.start()
            time.sleep(0.1)

        def stop(self):
            self._running = False
            if self._thread_id:
                PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            if self._hook_thread:
                self._hook_thread.join(timeout=2)
            self._hook       = None
            self._thread_id  = None


# ==================================================================
# macOS implementation
# ==================================================================

elif sys.platform == "darwin":
    import queue as _queue

    try:
        import Quartz
        _QUARTZ_OK = True
    except ImportError:
        _QUARTZ_OK = False
        print("[KeyboardHook] pyobjc-framework-Quartz not installed — "
              "pip install pyobjc-framework-Quartz")

    # CGKeyCode values for F1–F12
    _VK_F1  = 0x7A
    _VK_F2  = 0x78
    _VK_F3  = 0x63
    _VK_F4  = 0x76
    _VK_F5  = 0x60
    _VK_F6  = 0x61
    _VK_F7  = 0x62
    _VK_F8  = 0x64
    _VK_F9  = 0x65
    _VK_F10 = 0x6D
    _VK_F11 = 0x67
    _VK_F12 = 0x6F

    _VK_TO_EVENT = {
        _VK_F1:  "f1",
        _VK_F2:  "f2",
        _VK_F3:  "f3",
        _VK_F4:  "f4",
        _VK_F5:  "f5",
        _VK_F6:  "f6",
        _VK_F7:  "f7",
        _VK_F8:  "f8",
        _VK_F9:  "f9",
        _VK_F10: "f10",
        _VK_F11: "f11",
        _VK_F12: "f12",
    }

    class KeyboardHook:
        """
        Uses CGEventTap on macOS to intercept F1–F12 key presses and
        remap them to custom actions.
        Requires Accessibility permission (System Settings → Privacy & Security →
        Accessibility).
        """

        def __init__(self):
            self._running        = False
            self._callbacks      = {}
            self._blocked_events = set()
            self._tap            = None
            self._tap_source     = None
            self._dispatch_queue = _queue.Queue()
            self._dispatch_thread = None

        # ── binding API ───────────────────────────────────────

        def register(self, event_type, callback):
            self._callbacks.setdefault(event_type, []).append(callback)

        def block(self, event_type):
            self._blocked_events.add(event_type)

        def unblock(self, event_type):
            self._blocked_events.discard(event_type)

        def reset_bindings(self):
            self._callbacks.clear()
            self._blocked_events.clear()

        # ── dispatch ──────────────────────────────────────────

        def _dispatch(self, event):
            for cb in self._callbacks.get(event.event_type, []):
                try:
                    cb(event)
                except Exception as exc:
                    print(f"[KeyboardHook] callback error: {exc}")

        def _dispatch_loop(self):
            while self._running:
                try:
                    evt = self._dispatch_queue.get(timeout=0.5)
                    self._dispatch(evt)
                except Exception:
                    pass

        # ── CGEventTap callback ───────────────────────────────

        def _tap_callback(self, proxy, event_type, event, refcon):
            if not _QUARTZ_OK:
                return event
            try:
                if event_type == Quartz.kCGEventKeyDown:
                    vk = Quartz.CGEventGetIntegerValueField(
                        event, Quartz.kCGKeyboardEventKeycode)
                    evt_name = _VK_TO_EVENT.get(vk)
                    if evt_name and evt_name in self._blocked_events:
                        self._dispatch_queue.put(KeyboardEvent(evt_name))
                        return None   # suppress event
            except Exception as exc:
                print(f"[KeyboardHook] tap callback error: {exc}")
            return event

        # ── lifecycle ─────────────────────────────────────────

        def _run_tap(self):
            if not _QUARTZ_OK:
                return
            try:
                mask = (1 << Quartz.kCGEventKeyDown)
                self._tap = Quartz.CGEventTapCreate(
                    Quartz.kCGSessionEventTap,
                    Quartz.kCGHeadInsertEventTap,
                    Quartz.kCGEventTapOptionDefault,
                    mask,
                    self._tap_callback,
                    None,
                )
                if not self._tap:
                    print("[KeyboardHook] CGEventTap creation failed — "
                          "check Accessibility permission")
                    return

                self._tap_source = Quartz.CFMachPortCreateRunLoopSource(
                    None, self._tap, 0)
                loop = Quartz.CFRunLoopGetCurrent()
                Quartz.CFRunLoopAddSource(
                    loop, self._tap_source,
                    Quartz.kCFRunLoopCommonModes)
                Quartz.CGEventTapEnable(self._tap, True)
                print("[KeyboardHook] CGEventTap installed")
                self._running = True

                while self._running:
                    Quartz.CFRunLoopRunInMode(
                        Quartz.kCFRunLoopDefaultMode, 0.5, False)

                Quartz.CGEventTapEnable(self._tap, False)
            except Exception as exc:
                print(f"[KeyboardHook] run_tap error: {exc}")

        def start(self):
            self._running = True
            self._dispatch_thread = threading.Thread(
                target=self._dispatch_loop, daemon=True,
                name="KbdHookDispatch")
            self._dispatch_thread.start()
            tap_thread = threading.Thread(
                target=self._run_tap, daemon=True,
                name="KbdHookTap")
            tap_thread.start()
            time.sleep(0.1)

        def stop(self):
            self._running = False
            if self._tap:
                try:
                    Quartz.CGEventTapEnable(self._tap, False)
                except Exception:
                    pass
                self._tap = None


# ==================================================================
# Stub for unsupported platforms
# ==================================================================

else:
    class KeyboardHook:
        """No-op keyboard hook for unsupported platforms."""

        def __init__(self):
            self._callbacks      = {}
            self._blocked_events = set()

        def register(self, event_type, callback):
            self._callbacks.setdefault(event_type, []).append(callback)

        def block(self, event_type):
            self._blocked_events.add(event_type)

        def unblock(self, event_type):
            self._blocked_events.discard(event_type)

        def reset_bindings(self):
            self._callbacks.clear()
            self._blocked_events.clear()

        def start(self):
            pass

        def stop(self):
            pass
