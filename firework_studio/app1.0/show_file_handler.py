import numpy as np
import json
import os

from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor

from PyQt6.QtGui import QColor
from toaster import ToastDialog
from handles import FiringHandles
from analysis import AudioAnalysis

class FireworkshowManager:
    @staticmethod
    def save_show(file_path, audio_datas, sr, firework_times, segment_times, duration, handles):
        # Ensure music_dir is a sibling of the file, not inside the file name
        base_dir = os.path.dirname(os.path.abspath(file_path))
        music_dir = os.path.join(base_dir, "music")

        # Save audio_datas to this local 'music_dir' 
        audio_paths = []
        # Ensure the music directory exists
        if not os.path.exists(music_dir):
            try:
                os.makedirs(music_dir, exist_ok=True)
            except Exception as e:
                print(f"Error creating music directory: {e}")
                raise
        for idx, audio_data in enumerate(audio_datas):
            audio_file = os.path.join(music_dir, f"audio_{idx}.npy")
            try:
                np.save(audio_file, audio_data)
                audio_paths.append(audio_file)
            except Exception as e:
                print(f"Error saving audio file {audio_file}: {e}")
                raise

        # Convert handles to a list of lists using to_list() if available, and ensure all elements are JSON serializable
        def make_json_serializable(obj):
            import numpy as np
            if isinstance(obj, QColor):
                return obj.name()  # Convert QColor to hex string
            elif isinstance(obj, np.ndarray):
                return obj.tolist()  # Convert numpy arrays to lists
            elif isinstance(obj, np.integer):
                return int(obj)  # Convert numpy integers to Python int
            elif isinstance(obj, np.floating):
                return float(obj)  # Convert numpy floats to Python float
            elif isinstance(obj, (list, tuple)):
                return [make_json_serializable(x) for x in obj]
            elif isinstance(obj, dict):
                return {k: make_json_serializable(v) for k, v in obj.items()}
            elif hasattr(obj, '__dict__'):
                # Handle objects with attributes by converting to dict first
                return make_json_serializable(obj.__dict__)
            else:
                try:
                    if hasattr(obj, 'item'):
                        return obj.item()
                    return obj
                except (TypeError, AttributeError):
                    return str(obj)

        handles_list = []
        if isinstance(handles, list):
            for handle in handles:
                if hasattr(handle, "to_list"):
                    handle_data = handle.to_list()
                elif isinstance(handle, (list, tuple)):
                    handle_data = list(handle)
                else:
                    try:
                        handle_data = list(handle)
                    except Exception:
                        handle_data = [str(handle)]
                handle_data = make_json_serializable(handle_data)
                handles_list.append(handle_data)
        handles_list = make_json_serializable(handles_list)

        show_data = {
            "audio_paths": audio_paths,
            "sr": sr,
            "firework_times": make_json_serializable(firework_times),
            "segment_times": make_json_serializable(segment_times),
            "duration": duration,
            "handles": handles_list,
        }
        show_data = make_json_serializable(show_data)

        with open(file_path, "w") as f:
            json.dump(show_data, f, indent=2)

    @staticmethod
    def load_show(file_path):
        show_data = {}
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            print(f"File {file_path} does not exist or is empty.")
            return None, None, [], [], [], None, []
        try:
            with open(file_path, "r") as f:
                show_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {file_path}: {e}")
            return None, None, [], [], [], None, []
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None, None, [], [], [], None, []
        audio_paths = show_data.get("audio_paths", [])
        sr = show_data.get("sr", None)
        firework_times = show_data.get("firework_times", [])
        segment_times = show_data.get("segment_times", [])
        duration = show_data.get("duration", None)
        handles = show_data.get("handles", [])

        # Load audio_datas from local 'music' folder
        audio_datas = []
        audio_data = None
        if audio_paths:
            try:
                for audio_file in audio_paths:
                    if os.path.exists(audio_file):
                        audio_datas.append(np.load(audio_file))
                if audio_datas:
                    audio_data = audio_datas[0] if len(audio_datas) == 1 else np.concatenate(audio_datas)
                    if sr and audio_data is not None:
                        duration = audio_data.shape[0] / sr
            except Exception as e:
                print(f"Error loading audio files from local music folder: {e}")
                audio_datas = []
                audio_data = None
        else:
            print("No audio paths found in saved show data")
            audio_datas = []
            audio_data = None

        return audio_data, sr, audio_datas, firework_times, segment_times, duration, handles

class ShowFileHandler:
    def __init__(self, main_window, button_style):
        self.main_window = main_window
        self.button_style = button_style

    def save_show(self):
        if not self.main_window.audio_datas:
            ToastDialog("No show to save!", parent=self.main_window).show()
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window, "Save Firework Show", "", "Firework Show (*.fwshow);;All Files (*)"
        )
        if file_path:
            sr = self.main_window.sr
            firework_times = getattr(self.main_window.preview_widget, "firework_times", [])
            segment_times = self.main_window.segment_times
            duration = self.main_window.duration
            handles = []

            if hasattr(self.main_window.preview_widget, "get_handles"):
                raw_handles = self.main_window.preview_widget.get_handles()
                for handle in raw_handles:
                    handles.append(handle.to_list())

            try:
                FireworkshowManager.save_show(file_path, self.main_window.audio_datas, sr, firework_times, segment_times, duration, handles)
                def show_saved_toast():
                    toast = ToastDialog("Show saved!", parent=self.main_window)
                    geo = self.main_window.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2500, toast.close)
                show_saved_toast()
            except Exception as e:
                print(f"Error saving show: {e}")
                print(f"Handle data types: {[type(h) for h in handles]}")
                if handles:
                    print(f"First handle: {handles[0]}")
                ToastDialog(f"Error saving show: {str(e)}", parent=self.main_window).show()

    def load_show(self):
        self.main_window.fireworks_canvas.set_fireworks_enabled(False)
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Load Firework Show", "", "Firework Show (*.fwshow);;All Files (*)"
        )
        if file_path:
            audio_data, sr, audio_datas, firework_times, segment_times, duration, handles = FireworkshowManager.load_show(file_path)

            # Set the original audio paths from the saved show data
            with open(file_path, "r") as f:
                show_data = json.load(f)
            saved_audio_paths = show_data.get("audio_paths", [])
            self.main_window.paths = saved_audio_paths if isinstance(saved_audio_paths, list) else []

            # Concatenate multiple audio files if present (assumes that the padding was corrected before saving)
            if audio_datas and isinstance(audio_datas, list) and len(audio_datas) > 1:
                try:
                    dtype = audio_datas[0].dtype
                    audio_datas = [np.asarray(a, dtype=dtype) for a in audio_datas]
                    audio_data = np.concatenate(audio_datas)
                    duration = audio_data.shape[0] / sr if sr else None
                except Exception as e:
                    print(f"Error concatenating audio files: {e}")
                    audio_data = audio_datas[0] if audio_datas else None
            elif audio_datas and len(audio_datas) == 1:
                audio_data = audio_datas[0]

            self.main_window.audio_data = audio_data
            self.main_window.sr = sr
            self.main_window.audio_datas = audio_datas
            self.main_window.segment_times = segment_times
            self.main_window.duration = duration

            self.main_window.paths = saved_audio_paths if isinstance(saved_audio_paths, list) else []

            if hasattr(self.main_window, 'audio_loader'):
                self.main_window.audio_loader.paths = self.main_window.paths
            self.main_window.clear_show()
            self.main_window.preview_widget.set_show_data(audio_data, sr, segment_times, firework_times, duration)
            if audio_data is not None:
                basenames = []
                if self.main_window.paths:
                    basenames = [os.path.basename(str(p)) for p in self.main_window.paths if p and isinstance(p, (str, bytes, os.PathLike))]
                if basenames:
                    toast = ToastDialog(f"Loaded audio: {', '.join(basenames)}", parent=self.main_window)
                else:
                    toast = ToastDialog("Loaded show (audio paths not available)", parent=self.main_window)
                geo = self.main_window.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(2500, toast.close)
                self.main_window.update_firework_show_info()
            elif audio_data is None:
                self.main_window.status_bar.showMessage("No audio loaded.")

            loaded_handles = []
            if handles and isinstance(handles, list):
                for handle in handles:
                    try:
                        if isinstance(handle, list) and len(handle) > 0:
                            for i, val in enumerate(handle):
                                if isinstance(val, str) and val.startswith("#") and len(val) in (7, 9):
                                    handle[i] = QColor(val)
                        loaded_handles.append(FiringHandles.from_list(handle) if isinstance(handle, list) else handle)
                    except Exception as e:
                        print(f"Error reconstructing handle: {e}")
                        loaded_handles.append(handle)
            if hasattr(self.main_window.preview_widget, "set_handles"):
                self.main_window.preview_widget.set_handles(loaded_handles)

            fw_canvas = self.main_window.fireworks_canvas
            fw_canvas.reset_fireworks()
            for handle in loaded_handles:
                if hasattr(fw_canvas, "add_firework"):
                    fw_canvas.add_firework(handle)

            # this is setting up analysis and plotting to mimic load audio functionality
            self.main_window.analyzer = AudioAnalysis(audio_data,audio_datas, sr)
            self.main_window.audio_loader.connect_analysis_signals()
            self.main_window.plot_waveform()

            def show_loaded_toast():
                toast = ToastDialog("Show loaded!", parent=self.main_window)
                geo = self.main_window.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(2500, toast.close)
            show_loaded_toast()

            self.main_window.fireworks_canvas.reset_fireworks()
            self.main_window.fireworks_canvas.set_fireworks_enabled(True)

