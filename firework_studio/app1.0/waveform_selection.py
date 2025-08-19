from matplotlib.widgets import SpanSelector
from toaster import ToastDialog
from PyQt6.QtCore import QTimer
class WaveformSelectionTool:
    # Add a waveform panning/selection tool using matplotlib's SpanSelector
    def __init__(self, canvas, main_window=None):
        self.canvas = canvas
        self.ax = self.canvas.figure.axes[0]
        self.span = SpanSelector(
            self.ax,
            self.on_select,
            "horizontal",
            useblit=True,
            props=dict(alpha=0.3, facecolor="cyan"),
            interactive=True,
            drag_from_anywhere=True
        )
        self.selected_region = None
        self.main_window = main_window
        self._original_xlim = self.ax.get_xlim()

    def clear_selection(self, redraw=True):
        # Remove the highlighted selection area and restore original limits
        self.selected_region = None
        self.span.set_active(True)  # Ensure the span selector remains enabled
        # Remove the selection visual by deactivating and then reactivating the span selector
        self.span.set_active(False)
        self.ax.set_xlim(self._original_xlim)
        if redraw:
            self.canvas.draw_idle()
        if self.main_window and hasattr(self.main_window, "preview_widget"):
            self.main_window.preview_widget.reset_selected_region()
            self.main_window.preview_widget.update()
        if self.main_window and hasattr(self.main_window, "status_bar"):
            self.main_window.status_bar.showMessage(self.main_window.firework_show_info)
        # Reactivate the span selector for new selections
        self.span.set_active(True)
        if self.main_window and hasattr(self.main_window, "update_firework_show_info"):
            self.main_window.update_firework_show_info()

    def update_original_limits(self):
        """Update the stored original x-limits to match current axis limits"""
        # Ensure we have the correct axis reference
        if hasattr(self.canvas, 'figure') and hasattr(self.canvas.figure, 'axes') and self.canvas.figure.axes:
            self.ax = self.canvas.figure.axes[0]
        self._original_xlim = self.ax.get_xlim()

    def on_select(self, xmin, xmax):
        if abs(xmax - xmin) < 0.05:
            if self.main_window and hasattr(self.main_window, 'analyzer') and self.main_window.analyzer:
                self.main_window.analyzer.reset_selected_region()
            return
        self.selected_region = (xmin, xmax)
        # Update status bar and filter segments/firings if main_window is provided
        if self.main_window and hasattr(self.main_window, "status_bar"):
            def format_time(t):
                mins = int(t // 60)
                secs = int(t % 60)
                ms = int((t - int(t)) * 1000)
                return f"{mins:02d}:{secs:02d}:{ms:03d}"
            start = format_time(xmin)
            end = format_time(xmax)
            
            self.main_window.status_bar.showMessage(
                f"Selected region: {start} - {end}"
            )
            # Only update the selected region for visual feedback, do not filter or add firings
            self.main_window.preview_widget.set_selected_region((xmin, xmax))
            if self.main_window and hasattr(self.main_window, 'analyzer') and self.main_window.analyzer:
                self.main_window.analyzer.set_selected_region((xmin, xmax))
            self.main_window.preview_widget.update()
            self.ax.set_xlim(xmin, xmax)
            self.canvas.draw_idle()
