from __future__ import annotations

import ctypes
from ctypes import POINTER, byref, c_int32, c_uint32, c_void_p
from ctypes.util import find_library
from dataclasses import dataclass
from typing import Callable


UInt32 = c_uint32
OSStatus = c_int32
EventHotKeyRef = c_void_p
EventHandlerRef = c_void_p
EventTargetRef = c_void_p
EventRef = c_void_p


class EventTypeSpec(ctypes.Structure):
    _fields_ = [
        ("eventClass", UInt32),
        ("eventKind", UInt32),
    ]


class EventHotKeyID(ctypes.Structure):
    _fields_ = [
        ("signature", UInt32),
        ("id", UInt32),
    ]


def _four_char_code(text: str) -> int:
    return int.from_bytes(text.encode("latin-1"), "big")


CARBON_PATH = find_library("Carbon") or "/System/Library/Frameworks/Carbon.framework/Carbon"
CARBON = ctypes.cdll.LoadLibrary(CARBON_PATH)

CARBON.GetApplicationEventTarget.restype = EventTargetRef
CARBON.InstallEventHandler.argtypes = [
    EventTargetRef,
    ctypes.c_void_p,
    UInt32,
    POINTER(EventTypeSpec),
    c_void_p,
    POINTER(EventHandlerRef),
]
CARBON.InstallEventHandler.restype = OSStatus
CARBON.RegisterEventHotKey.argtypes = [
    UInt32,
    UInt32,
    EventHotKeyID,
    EventTargetRef,
    UInt32,
    POINTER(EventHotKeyRef),
]
CARBON.RegisterEventHotKey.restype = OSStatus
CARBON.UnregisterEventHotKey.argtypes = [EventHotKeyRef]
CARBON.UnregisterEventHotKey.restype = OSStatus
CARBON.RemoveEventHandler.argtypes = [EventHandlerRef]
CARBON.RemoveEventHandler.restype = OSStatus
CARBON.GetEventParameter.argtypes = [
    EventRef,
    UInt32,
    UInt32,
    c_void_p,
    UInt32,
    POINTER(UInt32),
    c_void_p,
]
CARBON.GetEventParameter.restype = OSStatus


kEventClassKeyboard = _four_char_code("keyb")
kEventHotKeyPressed = 6
kEventParamDirectObject = _four_char_code("----")
typeEventHotKeyID = _four_char_code("hkid")

cmdKey = 1 << 8
shiftKey = 1 << 9
optionKey = 1 << 11
controlKey = 1 << 12


KEY_CODES = {
    "A": 0,
    "S": 1,
    "D": 2,
    "F": 3,
    "H": 4,
    "G": 5,
    "Z": 6,
    "X": 7,
    "C": 8,
    "V": 9,
    "B": 11,
    "Q": 12,
    "W": 13,
    "E": 14,
    "R": 15,
    "Y": 16,
    "T": 17,
    "1": 18,
    "2": 19,
    "3": 20,
    "4": 21,
    "6": 22,
    "5": 23,
    "=": 24,
    "9": 25,
    "7": 26,
    "-": 27,
    "8": 28,
    "0": 29,
    "]": 30,
    "O": 31,
    "U": 32,
    "[": 33,
    "I": 34,
    "P": 35,
    "L": 37,
    "J": 38,
    "'": 39,
    "K": 40,
    ";": 41,
    "\\": 42,
    ",": 43,
    "/": 44,
    "N": 45,
    "M": 46,
    ".": 47,
    "SPACE": 49,
    "RETURN": 36,
    "ENTER": 76,
    "TAB": 48,
    "ESC": 53,
    "ESCAPE": 53,
}


MODIFIERS = {
    "META": cmdKey,
    "CTRL": controlKey,
    "ALT": optionKey,
    "SHIFT": shiftKey,
}


@dataclass(slots=True)
class ParsedShortcut:
    key_code: int
    modifiers: int


def parse_shortcut(shortcut: str) -> ParsedShortcut | None:
    primary = shortcut.split(",", 1)[0].strip()
    if not primary:
        return None

    modifiers = 0
    key_code: int | None = None
    for token in [part.strip() for part in primary.split("+") if part.strip()]:
        upper = token.upper()
        if upper in MODIFIERS:
            modifiers |= MODIFIERS[upper]
            continue
        key_code = KEY_CODES.get(upper)
        if key_code is None and len(token) == 1:
            key_code = KEY_CODES.get(token.upper())
    if key_code is None:
        return None
    return ParsedShortcut(key_code=key_code, modifiers=modifiers)


EventHandlerUPP = ctypes.CFUNCTYPE(OSStatus, c_void_p, EventRef, c_void_p)


class MacLauncherShortcut:
    def __init__(self, on_trigger: Callable[[], None]) -> None:
        self.on_trigger = on_trigger
        self._hot_key_ref = EventHotKeyRef()
        self._handler_ref = EventHandlerRef()
        self._handler_callback = EventHandlerUPP(self._handle_hotkey)
        self._hot_key_id = EventHotKeyID(signature=_four_char_code("SLFH"), id=1)
        self._install_handler()

    def _install_handler(self) -> None:
        event_spec = EventTypeSpec(kEventClassKeyboard, kEventHotKeyPressed)
        CARBON.InstallEventHandler(
            CARBON.GetApplicationEventTarget(),
            self._handler_callback,
            1,
            byref(event_spec),
            None,
            byref(self._handler_ref),
        )

    def register(self, shortcut: str) -> bool:
        parsed = parse_shortcut(shortcut)
        if parsed is None:
            return False
        self.unregister()
        status = CARBON.RegisterEventHotKey(
            parsed.key_code,
            parsed.modifiers,
            self._hot_key_id,
            CARBON.GetApplicationEventTarget(),
            0,
            byref(self._hot_key_ref),
        )
        return status == 0

    def unregister(self) -> None:
        if self._hot_key_ref:
            CARBON.UnregisterEventHotKey(self._hot_key_ref)
            self._hot_key_ref = EventHotKeyRef()

    def close(self) -> None:
        self.unregister()
        if self._handler_ref:
            CARBON.RemoveEventHandler(self._handler_ref)
            self._handler_ref = EventHandlerRef()

    def _handle_hotkey(self, _call_ref: c_void_p, event: EventRef, _user_data: c_void_p) -> int:
        hot_key_id = EventHotKeyID()
        size = UInt32()
        status = CARBON.GetEventParameter(
            event,
            kEventParamDirectObject,
            typeEventHotKeyID,
            None,
            ctypes.sizeof(hot_key_id),
            byref(size),
            byref(hot_key_id),
        )
        if status == 0 and hot_key_id.id == self._hot_key_id.id:
            self.on_trigger()
        return 0
