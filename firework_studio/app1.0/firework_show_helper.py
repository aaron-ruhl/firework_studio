import numpy as np
import librosa
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QComboBox, QSpinBox
from toaster import ToastDialog
import threading
import random

class MarkingStack:
    def __init__(self):
        self.stack = []
        self.redo_stack = []

    def push(self, marking_type, new_items):
        self.stack.append({'type': marking_type, 'items': list(new_items)})
        self.redo_stack.clear()  # Clear redo history on new action

    def undo(self):
        if self.stack:
            entry = self.stack.pop()
            self.redo_stack.append(entry)
            return entry if isinstance(entry, dict) else None
        return None

    def redo(self):
        if self.redo_stack:
            entry = self.redo_stack.pop()
            self.stack.append(entry)
            return entry if isinstance(entry, dict) else None
        return None

    def top(self):
        if self.stack:
            return self.stack[-1]
        return None

    def clear(self):
        self.stack.clear()
        self.redo_stack.clear()

    def get_all(self, marking_type):
        return [entry['items'] for entry in self.stack if entry['type'] == marking_type]

class FireworkShowHelper:
    def __init__(self, main_window):
        self.main_window = main_window
        self.marking_stack = MarkingStack()

    def _create_specific_handle_with_random_pattern(self, firing_time):
        """Create a specific handle with a random pattern for automatic firing addition."""
        patterns = [
            ("Circle", "circle"),
            ("Chrys", "chrysanthemum"),
            ("Palm", "palm"),
            ("Willow", "willow"),
            ("Peony", "peony"),
            ("Ring", "ring"),
            ("Rainbow", "rainbow"),
        ]
        # Choose a random pattern
        pattern_label, pattern_value = random.choice(patterns)
        
        # Create a specific handle list/tuple with the required parameters
        # Based on the add_firing method in fireworks_preview.py, it expects:
        # firing_time, color, number_firings, pattern, display_number
        specific_handle = [
            firing_time,
            None,  # Color will be assigned automatically by add_firing
            0,     # Display number will be assigned automatically
            pattern_value,  # Random pattern
            1      # Default number of firings
        ]
        return specific_handle

    def plot_spectrogram(self):
        def worker():
            mw = self.main_window
            ax = mw.spectrogram_ax
            ax.clear()
            if mw.audio_data is not None and mw.sr is not None:
                # Support for multiple audio tracks (list/tuple of arrays)
                audio_datas = mw.audio_data if isinstance(mw.audio_data, (list, tuple)) else [mw.audio_data]
                sr = mw.sr
                duration = max(len(ad) for ad in audio_datas) / sr  # Use max duration

                # Match max_points to waveform downsampling for consistent time axis
                max_points = 2000
                # Calculate n_fft and hop_length so that spectrogram time bins match waveform downsampling
                # waveform: factor = len(audio_data) // max_points
                # spectrogram: n_frames = 1 + (len(audio_data) - n_fft) // hop_length
                for idx, audio_data in enumerate(audio_datas):
                    factor = len(audio_data) // max_points if len(audio_data) > max_points else 1
                    # n_fft should be large enough for good freq resolution, but not too large
                    n_fft = min(2048, max(512, factor * 2))
                    hop_length = max(1, factor)
                    # Adjust center=False to align spectrogram with waveform (no padding)
                    S = np.abs(librosa.stft(audio_data, n_fft=n_fft, hop_length=hop_length, center=False))
                    S_db = librosa.amplitude_to_db(S, ref=np.max)
                    # Downsample spectrogram for plotting if too large
                    if S_db.shape[1] > max_points:
                        factor = S_db.shape[1] // max_points
                        S_db_ds = S_db[:, :factor * max_points].reshape(S_db.shape[0], -1, factor).mean(axis=2)
                    else:
                        S_db_ds = S_db
                        factor = 1
                    # Calculate time axis to match waveform
                    n_frames = S_db_ds.shape[1]
                    # Offset time axis by half window to better align with waveform
                    times = np.linspace(0, len(audio_data) / sr, n_frames, endpoint=False)
                    times += (n_fft / 2) / sr
                    extent = [times[0], times[-1], 0, sr // 2]
                    # Use different alpha for overlays
                    ax.imshow(
                        S_db_ds,
                        aspect='auto',
                        origin='lower',
                        cmap='magma',
                        extent=extent,
                        alpha=1.0 if len(audio_datas) == 1 else 0.7 - 0.2 * idx
                    )

                ax.set(
                    xlabel="Time (s)", ylabel="Frequency (Hz)"
                )
                # Ensure consistent time axis for all audio files
                ax.set_xlim(0, duration)
                ax.set_ylim(0, sr // 2)
                ax.grid(False)
                mw.spectrogram_canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            mw.spectrogram_canvas.draw_idle()

        threading.Thread(target=worker, daemon=True).start()

    def plot_waveform(self, current_legend=None):
        mw = self.main_window
        audio_to_plot = mw.audio_data
        ax = mw.waveform_canvas.figure.axes[0]
        ax.clear()
        if audio_to_plot is not None:
            times = np.linspace(0, len(audio_to_plot) / mw.sr, num=len(audio_to_plot))
            max_points = 2000
            if len(audio_to_plot) > max_points:
                factor = len(audio_to_plot) // max_points
                audio_data_reshaped = audio_to_plot[:factor * max_points].reshape(-1, factor)
                envelope_min = audio_data_reshaped.min(axis=1)
                envelope_max = audio_data_reshaped.max(axis=1)
                times_ds = times[:factor * max_points].reshape(-1, factor)
                times_ds = times_ds.mean(axis=1)
                ax.fill_between(times_ds, envelope_min, envelope_max, color="#8fb9bd", alpha=0.7, linewidth=0)
                ax.plot(times_ds, envelope_max, color="#5fd7e6", linewidth=0.7, alpha=0.9)
                ax.plot(times_ds, envelope_min, color="#5fd7e6", linewidth=0.7, alpha=0.9)
            else:
                ax.plot(times, audio_to_plot, color="#8fb9bd", linewidth=1.2, alpha=0.95, antialiased=True)
            ax.set_facecolor("#000000")
            ax.tick_params(axis='y', colors='white')
            mw.waveform_canvas.draw_idle()
            
            if hasattr(mw, 'waveform_selector'):
                mw.waveform_selector.update_original_limits()
            if mw.duration is not None and mw.sr is not None:
                ax.set_xlim(0, mw.duration)
            elif audio_to_plot is not None and mw.sr is not None:
                ax.set_xlim(0, len(audio_to_plot) / mw.sr)
            else:
                ax.set_xlim(0, 1)
            if hasattr(mw, 'waveform_selector') and hasattr(mw.waveform_selector, 'update_original_limits'):
                mw.waveform_selector.update_original_limits()
            ax.set_xlabel("Time (s)", color='white')
            ax.set_ylabel("Amplitude", color='white')
            ax.grid(True, color="#888888", alpha=0.3, linestyle="--", linewidth=0.8)
        else:
            ax.set_title("No audio loaded", color='white')
            ax.set_xticks([])
            ax.set_yticks([])
        if current_legend is not None:
            # When redrawing after undo/redo, just redraw existing markings without adding to stack
            self._redraw_markings_only()
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()
            
    def undo_last_marking(self):
        mw = self.main_window
        ax = mw.waveform_canvas.figure.axes[0]
        # Save current axis limits before undo
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        entry = self.marking_stack.undo()
        if entry is None:
            return
        marking_type = entry['type']
        items = entry['items']
        # Remove the specific items that were added in the last action
        if marking_type == 'segment' and hasattr(mw, 'segment_times') and mw.segment_times is not None:
            mw.segment_times = [t for t in mw.segment_times if t not in items]
            if not mw.segment_times:
                mw.segment_times = None
        elif marking_type == 'interesting' and hasattr(mw, 'points') and mw.points is not None:
            mw.points = [p for p in mw.points if p not in items]
            if not mw.points:
                mw.points = None
        elif marking_type == 'onset' and hasattr(mw, 'onsets') and mw.onsets is not None:
            mw.onsets = [o for o in mw.onsets if o not in items]
            if not mw.onsets:
                mw.onsets = None
        elif marking_type == 'peak' and hasattr(mw, 'peaks') and mw.peaks is not None:
            mw.peaks = [p for p in mw.peaks if p not in items]
            if not mw.peaks:
                mw.peaks = None
        # Redraw waveform to update markings
        self.plot_waveform(current_legend=True)
        # Restore axis limits to preserve zoom
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        mw.waveform_canvas.draw_idle()
        self.update_firework_show_info()

    def redo_last_marking(self):
        mw = self.main_window
        ax = mw.waveform_canvas.figure.axes[0]
        # Save current axis limits before redo
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        entry = self.marking_stack.redo()
        if entry is None:
            return
        marking_type = entry['type']
        items = entry['items']
        # Add items back, avoiding duplicates
        if marking_type == 'segment':
            if not hasattr(mw, 'segment_times') or mw.segment_times is None:
                mw.segment_times = []
            for t in items:
                if t not in mw.segment_times:
                    mw.segment_times.append(t)
        elif marking_type == 'interesting':
            if not hasattr(mw, 'points') or mw.points is None:
                mw.points = []
            for p in items:
                if p not in mw.points:
                    mw.points.append(p)
        elif marking_type == 'onset':
            if not hasattr(mw, 'onsets') or mw.onsets is None:
                mw.onsets = []
            for o in items:
                if o not in mw.onsets:
                    mw.onsets.append(o)
        elif marking_type == 'peak':
            if not hasattr(mw, 'peaks') or mw.peaks is None:
                mw.peaks = []
            for p in items:
                if p not in mw.peaks:
                    mw.peaks.append(p)
        # Redraw waveform to update markings
        self.plot_waveform(current_legend=True)
        # Restore axis limits to preserve zoom
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        mw.waveform_canvas.draw_idle()
        self.update_firework_show_info()

    def _redraw_markings_only(self):
        """Redraw markings without adding entries to the marking stack, preserving zoom/limits"""
        mw = self.main_window
        ax = mw.waveform_canvas.figure.axes[0]

        # Save current axis limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # Draw segments
        if mw.segment_times is not None and isinstance(mw.segment_times, (list, tuple)):
            for t in mw.segment_times:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label=None)
                elif isinstance(t, (np.ndarray, list, tuple)):
                    for tt in np.atleast_1d(t):
                        if isinstance(tt, (int, float)) and np.isscalar(tt) and not isinstance(tt, complex):
                            ax.axvline(x=float(tt), color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label=None)

        # Draw interesting points
        if mw.points is not None and isinstance(mw.points, (list, tuple, np.ndarray)):
            for t in mw.points:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ff6f00", linestyle=":", linewidth=1.5, alpha=0.8, label=None)

        # Draw onsets
        if mw.onsets is not None and isinstance(mw.onsets, (list, tuple, np.ndarray)):
            for t in mw.onsets:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#00ff6f", linestyle="-.", linewidth=1.5, alpha=0.8, label=None)

        # Draw peaks
        if mw.peaks is not None and isinstance(mw.peaks, (list, tuple, np.ndarray)):
            for t in mw.peaks:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ff00ff", linestyle="--", linewidth=1.5, alpha=0.8, label=None)

        # Update legend
        legend_labels = []
        if mw.segment_times is not None and len(mw.segment_times) > 0:
            ax.axvline(x=0, color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label="Segment")
            legend_labels.append("Segment")
        if mw.points is not None and len(mw.points) > 0:
            ax.axvline(x=0, color="#ff6f00", linestyle=":", linewidth=1.5, alpha=0.8, label="Interesting Point")
            legend_labels.append("Interesting Point")
        if mw.onsets is not None and len(mw.onsets) > 0:
            ax.axvline(x=0, color="#00ff6f", linestyle="-.", linewidth=1.5, alpha=0.8, label="Onset")
            legend_labels.append("Onset")
        if mw.peaks is not None and len(mw.peaks) > 0:
            ax.axvline(x=0, color="#ff00ff", linestyle="--", linewidth=1.5, alpha=0.8, label="Peak")
            legend_labels.append("Peak")

        if legend_labels:
            leg = ax.legend(
                loc="upper right",
                framealpha=0.3,
                fontsize=7,
                markerscale=0.7,
                handlelength=1.2,
                borderpad=0.3,
                labelspacing=0.2,
                handletextpad=0.3,
                borderaxespad=0.2,
            )
            if leg:
                leg.get_frame().set_alpha(0.3)

        # Restore previous axis limits to preserve zoom
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    def clear_all_markings(self):
        mw = self.main_window
        # Clear all marking data
        mw.segment_times = None
        mw.points = None
        mw.onsets = None
        mw.peaks = None
        self.marking_stack.clear()
        # Redraw waveform without markings
        self.plot_waveform(current_legend=True)
        # Update firework show info
        self.update_firework_show_info()
        
    def update_firework_show_info(self):
        mw = self.main_window
        if mw.duration is not None:
            mins, secs = divmod(int(mw.duration), 60)
            duration_str = f"{mins:02d}:{secs:02d}"
        else:
            duration_str = "N/A"
        firing_count = len(mw.preview_widget.firework_times) if hasattr(mw, "preview_widget") and hasattr(mw.preview_widget, "firework_times") and mw.preview_widget.firework_times is not None else 0
        pattern = "N/A"
        if hasattr(mw, "pattern_selector"):
            combo = mw.pattern_selector.findChild(QComboBox)
            if combo is not None:
                pattern = combo.currentText()
        number_firings = "N/A"
        if hasattr(mw, "firework_count_spinner_group"):
            spinner = mw.firework_count_spinner_group.findChild(QSpinBox)
            if spinner is not None:
                number_firings = spinner.value()
                
        if mw.segment_times and isinstance(mw.segment_times, (list, tuple)) and len(mw.segment_times) > 1:
            segment_count = len(mw.segment_times)  # N boundaries define N segments
        else:
            segment_count = 0
        mw.firework_show_info = (
            f"🎆 Pattern: {pattern} | "
            f"Amount: {number_firings} | "
            f"Firings: {firing_count} 🎆"
            f"   🎵 SR: {mw.sr if mw.sr is not None else 'N/A'} | "
            f"Duration: {duration_str} | "
            f"Segments: {segment_count}"
            f"🎵"
        )
        if hasattr(mw, "status_bar") and mw.status_bar is not None:
            mw.status_bar.showMessage(mw.firework_show_info)
            mw.status_bar.repaint()
        return

    def handle_segments(self, segment_times):
        mw = self.main_window
        if mw.segment_times is None or mw.segment_times == []:
            mw.segment_times = list(segment_times)
            new_segments = list(segment_times)
        else:
            new_segments = [s for s in segment_times if s not in mw.segment_times]
            mw.segment_times.extend(new_segments)
        
        self.marking_stack.push('segment', new_segments)

        # Add markings to current waveform
        ax = mw.waveform_canvas.figure.axes[0]
        if mw.segment_times is not None:
            for t in mw.segment_times:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label=None)
                elif isinstance(t, (np.ndarray, list, tuple)):
                    for tt in np.atleast_1d(t):
                        if isinstance(tt, (int, float)) and np.isscalar(tt) and not isinstance(tt, complex):
                            ax.axvline(x=float(tt), color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Segment" not in labels:
                ax.axvline(x=0, color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label="Segment")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)
        def show_segments_toast():
            # Calculate correct segment count: N boundaries define N-1 segments
            total_segments = len(mw.segment_times) if mw.segment_times and len(mw.segment_times) > 1 else 0
            toast = ToastDialog(f"Found {total_segments} segments!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        if hasattr(mw, "_segments_toast_shown") and not mw._segments_toast_shown:
            show_segments_toast()
            mw._segments_toast_shown = True
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()
        self.update_firework_show_info()

    def handle_interesting_points(self, points):
        mw = self.main_window
        if mw.points is None or mw.points == []:
            mw.points = list(points)
            new_points = list(points)
        else:
            new_points = [p for p in points if p not in mw.points]
            mw.points.extend(new_points)
        self.marking_stack.push('interesting', new_points)
        
        # Add firing handles for each new interesting point with random patterns
        for point_time in new_points:
            if isinstance(point_time, (int, float)) and np.isscalar(point_time) and not isinstance(point_time, complex):
                # Check if firing time is valid (greater than delay)
                if point_time >= mw.preview_widget.delay:
                    # Save current time and set to point time for add_firing
                    saved_time = mw.preview_widget.current_time
                    mw.preview_widget.current_time = float(point_time)
                    specific_handle = self._create_specific_handle_with_random_pattern(float(point_time))
                    mw.preview_widget.add_firing(specific_handle=specific_handle)
                    # Restore original time
                    mw.preview_widget.current_time = saved_time

        # Add markings to current waveform
        ax = mw.waveform_canvas.figure.axes[0]
        if mw.points is not None and isinstance(mw.points, (list, tuple, np.ndarray)):
            for t in mw.points:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ff6f00", linestyle=":", linewidth=1.5, alpha=0.8, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Interesting Point" not in labels:
                ax.axvline(x=0, color="#ff6f00", linestyle=":", linewidth=1.5, alpha=0.8, label="Interesting Point")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)
        def show_interesting_toast():
            toast = ToastDialog(f"Found {len(new_points)} interesting points!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        if hasattr(mw, "_interesting_points_toast_shown") and not mw._interesting_points_toast_shown:
            show_interesting_toast()
            mw._interesting_points_toast_shown = True
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()

    def handle_onsets(self, onsets):
        mw = self.main_window
        if mw.onsets is None or mw.onsets == []:
            mw.onsets = list(onsets)
            new_onsets = list(onsets)
        else:
            new_onsets = [o for o in onsets if o not in mw.onsets]
            mw.onsets.extend(new_onsets)
        self.marking_stack.push('onset', new_onsets)
        
        # Add firing handles for each new onset with random patterns
        for onset_time in new_onsets:
            if isinstance(onset_time, (int, float)) and np.isscalar(onset_time) and not isinstance(onset_time, complex):
                # Check if firing time is valid (greater than delay)
                if onset_time >= mw.preview_widget.delay:
                    # Save current time and set to onset time for add_firing
                    saved_time = mw.preview_widget.current_time
                    mw.preview_widget.current_time = float(onset_time)
                    specific_handle = self._create_specific_handle_with_random_pattern(float(onset_time))
                    mw.preview_widget.add_firing(specific_handle=specific_handle)
                    # Restore original time
                    mw.preview_widget.current_time = saved_time

        # Add markings to current waveform
        ax = mw.waveform_canvas.figure.axes[0]
        if mw.onsets is not None and isinstance(mw.onsets, (list, tuple, np.ndarray)):
            for t in mw.onsets:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#00ff6f", linestyle="-.", linewidth=1.5, alpha=0.8, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Onset" not in labels:
                ax.axvline(x=0, color="#00ff6f", linestyle="-.", linewidth=1.5, alpha=0.8, label="Onset")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)

        def show_onset_toast():
            toast = ToastDialog(f"Found {len(new_onsets)} onsets!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        if hasattr(mw, "_onsets_toast_shown") and not mw._onsets_toast_shown:
            show_onset_toast()
            mw._onsets_toast_shown = True
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()

    def handle_peaks(self, peaks):
        mw = self.main_window
        if mw.peaks is None or mw.peaks == []:
            mw.peaks = list(peaks)
            new_peaks = list(peaks)
        else:
            new_peaks = [p for p in peaks if p not in mw.peaks]
            mw.peaks.extend(new_peaks)
        self.marking_stack.push('peak', new_peaks)
        
        # Add firings for each new peak with random patterns
        for peak_time in new_peaks:
            if isinstance(peak_time, (int, float)) and np.isscalar(peak_time) and not isinstance(peak_time, complex):
                # Check if firing time is valid (greater than delay)
                if peak_time >= mw.preview_widget.delay:
                    # Save current time and set to peak time for add_firing
                    saved_time = mw.preview_widget.current_time
                    mw.preview_widget.current_time = float(peak_time)
                    specific_handle = self._create_specific_handle_with_random_pattern(float(peak_time))
                    mw.preview_widget.add_firing(specific_handle=specific_handle)
                    # Restore original time
                    mw.preview_widget.current_time = saved_time
        
        ax = mw.waveform_canvas.figure.axes[0]
        if mw.peaks is not None and isinstance(mw.peaks, (list, tuple, np.ndarray)):
            for t in mw.peaks:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ff00ff", linestyle="--", linewidth=1.5, alpha=0.8, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Peak" not in labels:
                ax.axvline(x=0, color="#ff00ff", linestyle="--", linewidth=1.5, alpha=0.8, label="Peak")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)

        def show_peaks_toast():
            toast = ToastDialog(f"Found {len(new_peaks)} peaks!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        # Ensure the attribute exists and is initialized
        if not hasattr(mw, "_peaks_toast_shown"):
            mw._peaks_toast_shown = False
        if mw._peaks_toast_shown is False:
            show_peaks_toast()
            mw._peaks_toast_shown = True
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()
