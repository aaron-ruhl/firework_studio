#!/usr/bin/env python3
"""
Test script to verify settings persistence
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from settings import SettingsDialog, SettingsManager

class DummyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Settings Persistence")
        self.analyzer = None

def test_settings_persistence():
    app = QApplication(sys.argv)
    
    # Create a dummy main window
    main_window = DummyMainWindow()
    
    # Create settings manager
    settings_manager = SettingsManager()
    
    print("=== Testing Settings Persistence ===")
    print("1. Creating first dialog with default settings...")
    
    # Create first dialog
    dialog1 = SettingsDialog(main_window)
    settings_manager.set_settings_dialog(dialog1)
    
    # Modify some settings
    dialog1.n_mfcc_spin.setValue(20)  # Change from default 13 to 20
    dialog1.min_segments_spin.setValue(5)  # Change from default 2 to 5
    dialog1.scoring_box.setCurrentText("absolute")  # Change from default "squared"
    
    print(f"   Modified n_mfcc to: {dialog1.n_mfcc_spin.value()}")
    print(f"   Modified min_segments to: {dialog1.min_segments_spin.value()}")
    print(f"   Modified scoring to: {dialog1.scoring_box.currentText()}")
    
    # Save settings
    settings_manager.save_current_settings()
    print("2. Settings saved!")
    
    # Get saved settings
    saved_settings = settings_manager.get_current_settings()
    print(f"3. Saved settings: n_mfcc={saved_settings['segment']['n_mfcc']}, "
          f"min_segments={saved_settings['segment']['min_segments']}, "
          f"scoring={saved_settings['peaks']['scoring']}")
    
    # Create second dialog - should load the saved settings
    print("4. Creating second dialog - should restore previous values...")
    dialog2 = SettingsDialog(main_window)
    settings_manager.set_settings_dialog(dialog2)
    
    print(f"   Restored n_mfcc: {dialog2.n_mfcc_spin.value()}")
    print(f"   Restored min_segments: {dialog2.min_segments_spin.value()}")
    print(f"   Restored scoring: {dialog2.scoring_box.currentText()}")
    
    # Verify the values were restored correctly
    success = (dialog2.n_mfcc_spin.value() == 20 and 
               dialog2.min_segments_spin.value() == 5 and
               dialog2.scoring_box.currentText() == "absolute")
    
    if success:
        print("✅ SUCCESS: Settings persistence is working correctly!")
    else:
        print("❌ FAILURE: Settings were not persisted correctly.")
    
    return success

if __name__ == "__main__":
    success = test_settings_persistence()
    sys.exit(0 if success else 1)
