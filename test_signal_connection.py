#!/usr/bin/env python3
"""
Simple test to verify that the handles_changed signal is properly connected
and that update_firework_show_info is called when handles change.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'firework_studio', 'app1.0'))

from PyQt6.QtWidgets import QApplication
from fireworks_preview import FireworkPreviewWidget
from firework_show_helper import FireworkShowHelper
from handles import FiringHandles

class MockMainWindow:
    """Mock main window for testing"""
    def __init__(self):
        self.audio_data = None
        self.sr = 44100
        self.duration = 10.0
        self.segment_times = []
        self.points = []
        self.onsets = []
        self.peaks = []
        self.firework_times = []
        self.update_count = 0
    
    def mock_update_info(self):
        self.update_count += 1
        print(f"update_firework_show_info called {self.update_count} times")

def test_signal_connection():
    app = QApplication([])
    
    # Create mock main window
    main_window = MockMainWindow()
    
    # Create preview widget and helper
    preview_widget = FireworkPreviewWidget()
    helper = FireworkShowHelper(main_window)
    
    # Replace the helper's method with our mock
    helper.update_firework_show_info = main_window.mock_update_info
    
    # Connect the signal (simulating what happens in the main window)
    preview_widget.handles_changed.connect(lambda handles: helper.update_firework_show_info())
    
    # Test 1: set_handles should trigger the signal
    print("Test 1: Testing set_handles...")
    test_handles = [
        FiringHandles(2.0, (255, 0, 0), number_firings=1, pattern="circle", display_number=1),
        FiringHandles(5.0, (0, 255, 0), number_firings=2, pattern="palm", display_number=2)
    ]
    preview_widget.set_handles(test_handles)
    
    # Test 2: add_time should trigger the signal
    print("Test 2: Testing add_time...")
    preview_widget.audio_data = [0] * 44100  # 1 second of silence
    preview_widget.sr = 44100
    preview_widget.duration = 10.0
    preview_widget.current_time = 2.0  # Set to 2.0 seconds (above the 1.8 delay threshold)
    preview_widget.add_time()
    
    # Test 3: reset_fireworks should trigger the signal
    print("Test 3: Testing reset_fireworks...")
    preview_widget.reset_fireworks()
    
    print(f"\nTotal calls to update_firework_show_info: {main_window.update_count}")
    print("Expected: 3 calls (set_handles, add_time, reset_fireworks)")
    
    if main_window.update_count == 3:
        print("✅ Test passed! Signal connection is working correctly.")
        return True
    else:
        print("❌ Test failed! Signal connection may not be working properly.")
        return False

if __name__ == "__main__":
    success = test_signal_connection()
    sys.exit(0 if success else 1)
