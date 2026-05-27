from ledger import MacroManager

def test_macro_list(macro_manager):
    macros = macro_manager.list_macros()
    assert len(macros) >= 3

def test_add_remove_macro(macro_manager):
    macro_manager.add_macro("testmacro", "TestDr", "TestCr")
    assert macro_manager.get("testmacro") is not None
    macro_manager.remove_macro("testmacro")
    assert macro_manager.get("testmacro") is None

def test_macro_persistence(macro_manager, temp_dir):
    macro_manager.add_macro("persist", "Pdr", "Pcr")
    new_mgr = MacroManager()
    assert new_mgr.get("persist") is not None