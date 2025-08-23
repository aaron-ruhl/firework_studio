#!/usr/bin/env python3
"""
Test script to verify undo/redo functionality works correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'firework_studio', 'app1.0'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from fireworks_preview import FireworkPreviewWidget, HandlesStack
from handles import FiringHandles
from PyQt6.QtGui import QColor

def test_undo_redo():
    app = QApplication(sys.argv)
    
    # Create a preview widget
    preview = FireworkPreviewWidget()
    
    # Set up some basic properties
    preview.duration = 10.0
    preview.audio_data = [0.0] * 44100  # Dummy audio data
    preview.sr = 44100
    preview.current_time = 2.0
    
    print("Starting undo/redo test...")
    
    # Test 1: Check initial state
    assert len(preview.fireworks) == 0, "Should start with no fireworks"
    assert len(preview.handles_stack.undo_stack) == 0, "Undo stack should be empty initially"
    assert len(preview.handles_stack.redo_stack) == 0, "Redo stack should be empty initially"
    print("✓ Initial state correct")
    
    # Test 2: Add a firework (should push to undo stack)
    preview.current_time = 3.0
    preview.add_time()
    assert len(preview.fireworks) == 1, "Should have 1 firework after adding"
    assert len(preview.handles_stack.undo_stack) == 1, "Undo stack should have 1 entry after adding"
    print("✓ Adding firework works and pushes to undo stack")
    
    # Test 3: Add another firework
    preview.current_time = 5.0
    preview.add_time()
    assert len(preview.fireworks) == 2, "Should have 2 fireworks after adding second"
    assert len(preview.handles_stack.undo_stack) == 2, "Undo stack should have 2 entries"
    print("✓ Adding second firework works")
    
    # Test 4: Undo should restore to previous state (1 firework)
    preview.undo()
    assert len(preview.fireworks) == 1, "Should have 1 firework after undo"
    assert len(preview.handles_stack.undo_stack) == 1, "Undo stack should have 1 entry after undo"
    assert len(preview.handles_stack.redo_stack) == 1, "Redo stack should have 1 entry after undo"
    print("✓ Undo works correctly")
    
    # Test 5: Redo should restore the second firework
    preview.redo()
    assert len(preview.fireworks) == 2, "Should have 2 fireworks after redo"
    assert len(preview.handles_stack.undo_stack) == 2, "Undo stack should have 2 entries after redo"
    assert len(preview.handles_stack.redo_stack) == 0, "Redo stack should be empty after redo"
    print("✓ Redo works correctly")
    
    # Test 6: Undo twice should go back to empty state
    preview.undo()  # Back to 1 firework
    preview.undo()  # Back to 0 fireworks
    assert len(preview.fireworks) == 0, "Should have 0 fireworks after undoing twice"
    assert len(preview.handles_stack.undo_stack) == 0, "Undo stack should be empty"
    assert len(preview.handles_stack.redo_stack) == 2, "Redo stack should have 2 entries"
    print("✓ Multiple undos work correctly")
    
    # Test 7: Remove operation should also be undoable
    preview.redo()  # Back to 1 firework
    preview.redo()  # Back to 2 fireworks
    preview.selected_firing = 0
    preview.remove_selected_firing()
    assert len(preview.fireworks) == 1, "Should have 1 firework after removing"
    assert len(preview.handles_stack.undo_stack) == 3, "Undo stack should have 3 entries (add, add, remove)"
    print("✓ Remove operation pushes to undo stack")
    
    # Test 8: Undo remove operation
    preview.undo()
    assert len(preview.fireworks) == 2, "Should have 2 fireworks after undoing remove"
    print("✓ Undoing remove operation works")
    
    # Test 9: Clear undo history
    preview.clear_undo_history()
    assert len(preview.handles_stack.undo_stack) == 0, "Undo stack should be empty after clearing"
    assert len(preview.handles_stack.redo_stack) == 0, "Redo stack should be empty after clearing"
    print("✓ Clear undo history works")
    
    print("\n🎆 All undo/redo tests passed! 🎆")
    
    app.quit()

if __name__ == "__main__":
    test_undo_redo()
