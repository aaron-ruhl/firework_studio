from matplotlib.widgets import SpanSelector

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

    def on_select(self, xmin, xmax):
        # If the region is too narrow (e.g., a click, not a drag), reset selection
        if abs(xmax - xmin) < 1e-3:
            self.selected_region = None
            if self.main_window and hasattr(self.main_window, "preview_widget"):
                self.main_window.preview_widget.reset_selected_region()
                self.main_window.preview_widget.update()
            if self.main_window and hasattr(self.main_window, "status_bar"):
                self.main_window.status_bar.showMessage("Selection cleared")
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
            self.main_window.preview_widget.update()

    def clear_selection(self):
        self.selected_region = None
        self.span.set_visible(False)
        self.canvas.draw_idle()
