from tools.telegram import TelegramDesktopMessenger


def test_contact_alias_resolution():
    messenger = TelegramDesktopMessenger(contacts={"دوستم": "Mostafa Test"})
    assert messenger._resolve_contact("دوستم") == "Mostafa Test"
    assert messenger._resolve_contact("دوستم ") == "Mostafa Test"
    assert messenger._resolve_contact("Ali Reza") == "Ali Reza"


def test_contact_aliases_are_optional():
    messenger = TelegramDesktopMessenger()
    assert messenger.contact_aliases() == []
    assert messenger._resolve_contact("  Test   Person ") == "Test Person"
