from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path


class TelegramDesktopMessenger:
    """Drive Telegram Desktop exactly like a user would on Windows.

    The interaction deliberately stays visible for the course demo:

        Win -> type Telegram -> Enter
        Telegram -> Esc Esc -> Ctrl+F
        paste contact -> Down -> Enter
        paste message -> Enter

    This implementation intentionally keeps the working V2 interaction model.
    It does *not* use a Telegram bot, credentials, image recognition, or a
    strict foreground gate.  A direct executable launch is only a fallback if
    Windows Search does not result in a Telegram process.
    """

    def __init__(
        self,
        executable: str = "",
        contacts: Mapping[str, str] | None = None,
        *,
        launch_mode: str = "windows_search",
        launch_wait_seconds: float = 3.0,
        search_wait_seconds: float = 1.6,
        chat_wait_seconds: float = 0.9,
    ) -> None:
        self.executable = executable.strip()
        self.contacts = {
            str(k).strip(): str(v).strip()
            for k, v in (contacts or {}).items()
            if str(k).strip() and str(v).strip()
        }
        self.launch_mode = launch_mode.strip().casefold() or "windows_search"
        self.launch_wait_seconds = max(0.5, float(launch_wait_seconds))
        self.search_wait_seconds = max(0.4, float(search_wait_seconds))
        self.chat_wait_seconds = max(0.3, float(chat_wait_seconds))

    def contact_aliases(self) -> list[str]:
        return sorted(self.contacts)

    def _resolve_contact(self, contact: str) -> str:
        contact = " ".join(contact.split()).strip()
        if not contact:
            return ""
        direct = self.contacts.get(contact)
        if direct:
            return direct
        lowered = contact.casefold()
        for alias, search_name in self.contacts.items():
            if alias.casefold() == lowered:
                return search_name
        return contact

    def _find_executable(self) -> Path | None:
        candidates: list[Path] = []
        if self.executable:
            candidates.append(Path(os.path.expandvars(os.path.expanduser(self.executable))))

        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if appdata:
            candidates.append(Path(appdata) / "Telegram Desktop" / "Telegram.exe")
        if localappdata:
            candidates.extend(
                [
                    Path(localappdata) / "Programs" / "Telegram Desktop" / "Telegram.exe",
                    Path(localappdata) / "Telegram Desktop" / "Telegram.exe",
                ]
            )

        which = shutil.which("Telegram.exe") or shutil.which("telegram")
        if which:
            candidates.append(Path(which))

        for candidate in candidates:
            try:
                if candidate.is_file():
                    return candidate.resolve()
            except OSError:
                continue
        return None

    @staticmethod
    def _telegram_pids() -> set[int]:
        try:
            import psutil
        except ImportError:
            return set()

        pids: set[int] = set()
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").casefold()
                if name in {"telegram.exe", "telegram"}:
                    pids.add(int(proc.info["pid"]))
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError, TypeError, ValueError):
                continue
        return pids

    @staticmethod
    def _focus_window_for_pids(pids: set[int]) -> bool:
        """Best-effort focus only; failure never cancels the working V2 flow."""
        if platform.system().lower() != "windows" or not pids:
            return False

        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            handles: list[int] = []
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

            @WNDENUMPROC
            def enum_proc(hwnd, _lparam):
                if not user32.IsWindowVisible(hwnd):
                    return True
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if int(pid.value) in pids and user32.GetWindowTextLengthW(hwnd) > 0:
                    handles.append(int(hwnd))
                return True

            user32.EnumWindows(enum_proc, 0)
            if not handles:
                return False

            hwnd = handles[0]
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE

            # This small Alt pulse improves SetForegroundWindow reliability on
            # Windows without changing Telegram state.
            VK_MENU = 0x12
            KEYEVENTF_KEYUP = 0x0002
            user32.keybd_event(VK_MENU, 0, 0, 0)
            user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
            user32.SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False

    def _wait_for_telegram_process(self, timeout: float) -> set[int]:
        deadline = time.monotonic() + max(0.5, timeout)
        pids: set[int] = set()
        while time.monotonic() < deadline:
            pids = self._telegram_pids()
            if pids:
                return pids
            time.sleep(0.15)
        return pids

    def _open_with_windows_search(self) -> tuple[bool, str]:
        """The exact visible V2-style launch, with a slightly larger delay."""
        import pyautogui
        import pyperclip

        # V2 used the Start/Windows key and pyautogui.write. Keep that as the
        # primary path because it is known to work on the course machine.
        pyautogui.press("win")
        time.sleep(0.75)
        pyautogui.write("Telegram", interval=0.055)
        time.sleep(0.85)
        pyautogui.press("enter")

        pids = self._wait_for_telegram_process(max(5.0, self.launch_wait_seconds + 2.0))
        if pids:
            time.sleep(self.launch_wait_seconds)
            self._focus_window_for_pids(pids)
            time.sleep(0.35)
            return True, "Windows Search -> Telegram"

        # Some Windows keyboard layouts/IME states can prevent write() from
        # entering Latin text. Retry the same *visible* Start search once using
        # clipboard paste before falling back to the executable.
        pyautogui.press("esc")
        time.sleep(0.25)
        pyperclip.copy("Telegram")
        pyautogui.press("win")
        time.sleep(0.75)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.85)
        pyautogui.press("enter")

        pids = self._wait_for_telegram_process(max(5.0, self.launch_wait_seconds + 2.0))
        if pids:
            time.sleep(self.launch_wait_seconds)
            self._focus_window_for_pids(pids)
            time.sleep(0.35)
            return True, "Windows Search -> Telegram (clipboard retry)"

        return False, "Windows Search did not start Telegram Desktop."

    def _open_and_focus(self) -> tuple[bool, str]:
        if self.launch_mode == "windows_search":
            try:
                opened, detail = self._open_with_windows_search()
                if opened:
                    return True, detail
            except Exception as exc:
                search_error = f"Windows Search launch failed: {exc}"
            else:
                search_error = detail
        else:
            search_error = "Windows Search launch disabled."

        # Functional fallback: if Windows Search is slow/broken, still complete
        # the command by launching the installed Telegram executable directly.
        executable = self._find_executable()
        if executable is None:
            return False, (
                f"{search_error} Telegram Desktop was not found. Install Telegram Desktop or set "
                "telegram_desktop_executable in config.json."
            )

        existing = self._telegram_pids()
        if existing:
            self._focus_window_for_pids(existing)
            time.sleep(0.6)
            return True, f"Focused existing Telegram: {executable}"

        try:
            subprocess.Popen([str(executable)], shell=False)
        except OSError as exc:
            return False, f"Could not start Telegram Desktop: {exc}"

        pids = self._wait_for_telegram_process(max(6.0, self.launch_wait_seconds + 3.0))
        if not pids:
            return False, "Telegram executable was launched, but no Telegram process appeared."
        time.sleep(self.launch_wait_seconds)
        self._focus_window_for_pids(pids)
        time.sleep(0.5)
        return True, f"Direct executable fallback: {executable}"

    def send(self, contact: str, message: str) -> dict[str, object]:
        if platform.system().lower() != "windows":
            return {
                "ok": False,
                "error": "Telegram Desktop UI automation is currently implemented for Windows only.",
            }

        search_name = self._resolve_contact(contact)
        message = message.strip()
        if not search_name:
            return {"ok": False, "error": "Telegram contact name is empty."}
        if not message:
            return {"ok": False, "error": "Message is empty."}
        if len(search_name) > 180:
            return {"ok": False, "error": "Contact name is unexpectedly long."}
        if len(message) > 3500:
            return {"ok": False, "error": "Message is too long for this assistant action."}

        try:
            import pyautogui
            import pyperclip
        except ImportError:
            return {
                "ok": False,
                "error": "Desktop automation dependencies are missing. Run: pip install pyautogui pyperclip",
            }

        pyautogui.FAILSAFE = True
        old_clipboard: str | None = None
        steps: list[str] = []

        try:
            try:
                old_clipboard = pyperclip.paste()
            except Exception:
                old_clipboard = None

            opened, launch_detail = self._open_and_focus()
            if not opened:
                return {"ok": False, "error": launch_detail, "steps": steps}
            steps.append(launch_detail)

            # Exact interaction sequence from the V2 implementation that worked
            # on the target machine. ORBIT's own interrupt shortcut is F8 in the
            # final UI, so these Escape keys cannot cancel the assistant.
            pyautogui.press("esc", presses=2, interval=0.12)
            time.sleep(0.30)
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.35)
            steps.append("Telegram search opened")

            pyperclip.copy(search_name)
            pyautogui.hotkey("ctrl", "a")
            pyautogui.hotkey("ctrl", "v")
            time.sleep(self.search_wait_seconds)
            steps.append(f"Contact searched: {search_name}")

            pyautogui.press("down")
            time.sleep(0.12)
            pyautogui.press("enter")
            time.sleep(self.chat_wait_seconds)
            steps.append("First matching chat opened")

            pyperclip.copy(message)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.20)
            steps.append("Message pasted")

            pyautogui.press("enter")
            time.sleep(0.35)
            steps.append("Send key pressed")

            return {
                "ok": True,
                "contact": contact.strip(),
                "telegram_search": search_name,
                "message": message,
                "method": "telegram_desktop_ui_v2_flow",
                "steps": steps,
            }
        except pyautogui.FailSafeException:
            return {
                "ok": False,
                "cancelled": True,
                "error": "Telegram automation was cancelled by the PyAutoGUI fail-safe.",
                "steps": steps,
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": f"Telegram Desktop automation failed: {exc}",
                "steps": steps,
            }
        finally:
            if old_clipboard is not None:
                try:
                    pyperclip.copy(old_clipboard)
                except Exception:
                    pass
