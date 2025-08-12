import random
import numpy as np
import json
import os

from PyQt6.QtWidgets import QPushButton, QFileDialog, QRadioButton
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QIcon

from toaster import ToastDialog
from handles import FiringHandles

class FireworkShowManager:
    """
    Handles saving and loading of firework show data (firings, segments, etc.)
    """

    @staticmethod
    def save_show(filepath, audio_data, firings, segment_times=None, sr=None, duration=None, background=None, background_path=None, fireworks_colors=None, handles=None):
        """
        Save the firework show data to a file (JSON format).
        """
        # Convert numpy array to list for JSON serialization
        audio_data_serializable = audio_data.tolist() if isinstance(audio_data, np.ndarray) else audio_data
        # Serialize handles as list of lists (assume FiringHandles has a to_list() method or similar)
        handles_serializable = []
        if handles is not None:
            for h in handles:
                # If FiringHandles has a to_list method, use it, else serialize __dict__ values
                if hasattr(h, "to_list"):
                    handles_serializable.append(h.to_list())
                else:
                    handles_serializable.append(list(h.__dict__.values()))
        show_data = {
            "firings": firings,
            "segment_times": segment_times if segment_times is not None else [],
            "sample_rate": sr,
            "duration": duration,
            "audio_data": audio_data_serializable,  # Now serializable
            "background": background,
            "background_path": background_path,
            "handles": handles_serializable,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(show_data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_show(filepath):
        """
        Load the firework show data from a file (JSON format).
        Returns: firings, segment_times, sr, duration, audio_data, background, background_path, handles
        """
        with open(filepath, "r", encoding="utf-8") as f:
            show_data = json.load(f)
        firings = show_data.get("firings", [])
        segment_times = show_data.get("segment_times", [])
        sr = show_data.get("sample_rate", None)
        duration = show_data.get("duration", None)
        audio_data = show_data.get("audio_data", None)
        background = show_data.get("background", None)
        background_path = show_data.get("background_path", None)
        handles_list = show_data.get("handles", [])
        if audio_data is not None:
            # Convert audio data from list to numpy array if needed
            audio_data = np.array(audio_data)
        # Recreate handles as FiringHandles objects from list of lists
        handles = []
        for h in handles_list:
            # If FiringHandles takes all values as positional args
            handles.append(FiringHandles(*h))
        return firings, segment_times, sr, duration, audio_data, background, background_path, handles

class ShowFileHandler:
    def __init__(self, main_window, button_style):
        self.main_window = main_window
        self.button_style = button_style

    def create_save_btn(self):
        btn = QPushButton("Save Show")
        btn.setStyleSheet(self.button_style)
        btn.clicked.connect(self.save_show)
        return btn

    def create_load_show_btn(self):
        btn = QPushButton("Load Show")
        btn.setStyleSheet(self.button_style)
        btn.clicked.connect(self.load_show)
        return btn

    def save_show(self):
        mw = self.main_window
        options = QFileDialog.Option(0)
        file_path, _ = QFileDialog.getSaveFileName(
            mw, "Save Firework Show", "", "Firework Show (*.json);;All Files (*)", options=options
        )
        if file_path:
            fireworks_colors = getattr(mw.preview_widget, "fireworks_colors", None)
            audio_data_to_save = (
                mw.audio_data.tolist() if isinstance(mw.audio_data, np.ndarray) else mw.audio_data
            )
            firings_to_save = (
                [float(t) for t in getattr(mw.preview_widget, "firework_firing", [])] if hasattr(mw.preview_widget, "firework_firing") else []
            )
            segment_times_to_save = (
                [float(t) for t in mw.segment_times] if mw.segment_times is not None else []
            )
            # Get handles from preview_widget if available
            handles_to_save = getattr(mw.preview_widget, "handles", None)
            FireworkShowManager.save_show(
                file_path,
                audio_data_to_save,
                firings_to_save,
                segment_times_to_save,
                mw.sr,
                mw.duration,
                background=bg,
                background_path=bg_path,
                fireworks_colors=fireworks_colors,
                handles=handles_to_save,
            )
            toast = ToastDialog("Show saved!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2000, toast.close)

    def load_show(self):
        mw = self.main_window
        options = QFileDialog.Option(0)
        file_path, _ = QFileDialog.getOpenFileName(
            mw, "Load Firework Show", "", "Firework Show (*.json);;All Files (*)", options=options
        )
        if file_path:
            firings, segment_times, sr, duration, audio_data_loaded, background, background_path, handles = FireworkShowManager.load_show(file_path)
            mw.firework_firing = [float(t) for t in firings] if firings is not None else []
            mw.segment_times = [float(t) for t in segment_times] if segment_times is not None else []
            mw.sr = int(sr) if sr is not None else None
            mw.duration = float(duration) if duration is not None else None
            if isinstance(audio_data_loaded, list):
                mw.audio_data = np.array(audio_data_loaded, dtype=np.float32)
            elif isinstance(audio_data_loaded, np.ndarray):
                mw.audio_data = audio_data_loaded.astype(np.float32)
            else:
                mw.audio_data = None
            mw.plot_waveform()
            mw.fireworks_colors = [
                QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                for _ in mw.firework_firing
            ]
            mw.preview_widget.set_fireworks_colors(mw.fireworks_colors)
            mw.preview_widget.set_show_data(
                mw.audio_data, mw.sr, mw.segment_times, mw.firework_firing, mw.duration
            )
            if hasattr(mw.preview_widget, "firework_firing"):
                mw.preview_widget.firework_firing = list(mw.firework_firing)
            # Set handles if set_handles exists and handles were loaded
            if hasattr(mw.preview_widget, "set_handles") and handles:
                mw.preview_widget.set_handles(handles)
            if background:
                if background == "custom" and background_path:
                    mw.fireworks_canvas.set_background("custom", background_path)
                    for btn_radio in mw.background_btn.findChildren(QRadioButton):
                        if btn_radio.text().lower() == "custom":
                            btn_radio.setChecked(True)
                            break
                else:
                    mw.fireworks_canvas.set_background(background)
                    for btn_radio in mw.background_btn.findChildren(QRadioButton):
                        if btn_radio.text().replace(" ", "").lower() == background.replace(" ", "").lower():
                            btn_radio.setChecked(True)
                            break
            mw.fireworks_canvas.update_animation()
            mw.update_firework_show_info()
            mw.preview_widget.update()
            mw.preview_widget.repaint()
            toast = ToastDialog("Show loaded!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2000, toast.close)