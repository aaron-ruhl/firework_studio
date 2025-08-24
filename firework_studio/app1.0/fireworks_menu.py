import os

from PyQt6.QtWidgets import QMenuBar, QMenu, QInputDialog, QVBoxLayout, QPushButton
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QTimer

from toaster import ToastDialog
from filter_dialog import FilterDialog
from filters import AudioFilter

class MenuBarHelper:
    def __init__(self, main_window, button_style, menu_style):
        self.main_window = main_window
        self.button_style = button_style
        self.menu_style = menu_style
        self.create_menus(self.main_window.analyzer)
    def update_status_bar(self):
        self.main_window.firework_show_helper.update_firework_show_info()
        self.main_window.status_bar.showMessage(self.main_window.firework_show_info)

    def create_menus(self, analyzer):
        mw = self.main_window
        
        ############################
        # File Menu                #
        ############################

        if mw.menuBar() is None:
            mw.setMenuBar(QMenuBar(mw))
        file_menu = mw.menuBar().addMenu("&File") #type: ignore
        if file_menu is not None:
            mw.menuBar().setStyleSheet(self.menu_style) #type: ignore
            save_action = QAction(QIcon(os.path.join("icons", "save.png")), "Save...", mw)
            save_action.setShortcut("Ctrl+S")
            save_action.triggered.connect(mw.save_btn.click)
            save_action.hovered.connect(self.update_status_bar)
            file_menu.addAction(save_action)

            load_action = QAction(QIcon(os.path.join("icons", "load.png")), "Open...", mw)
            load_action.setShortcut("Ctrl+O")
            load_action.triggered.connect(mw.load_show_btn.click)
            load_action.hovered.connect(self.update_status_bar)
            file_menu.addAction(load_action)

            clear_action = QAction(QIcon(os.path.join("icons", "clear-show.png")), "Clear Show", mw)
            clear_action.setShortcut("C")
            clear_action.triggered.connect(mw.clear_btn.click)
            clear_action.hovered.connect(self.update_status_bar)
            file_menu.addAction(clear_action)

            file_menu.addSeparator()

            exit_action = QAction(QIcon(os.path.join("icons", "exit.png")), "Exit", mw)
            exit_action.setShortcut("Ctrl+Q")
            exit_action.triggered.connect(mw.close)
            exit_action.hovered.connect(self.update_status_bar)
            file_menu.addAction(exit_action)

        ############################
        # Edit Menu                #
        ############################

        edit_menu = mw.menuBar().addMenu("&Edit") #type: ignore
        if edit_menu is not None:
            play_pause_action = QAction(QIcon(os.path.join("icons", "play.png")), "Play/Pause", mw)
            play_pause_action.setShortcut("Space")
            play_pause_action.triggered.connect(lambda: mw.play_pause_btn.toggle())
            play_pause_action.hovered.connect(self.update_status_bar)
            edit_menu.addAction(play_pause_action)

            stop_action = QAction(QIcon(os.path.join("icons", "stop.png")), "Stop", mw)
            stop_action.setShortcut("S")
            stop_action.triggered.connect(mw.stop_btn.click)
            stop_action.hovered.connect(self.update_status_bar)
            edit_menu.addAction(stop_action)

            load_audio_action = QAction(QIcon(os.path.join("icons", "upload.png")), "Load Audio...", mw)
            load_audio_action.setShortcut("Ctrl+L")
            load_audio_action.triggered.connect(mw.load_btn.click)
            load_audio_action.hovered.connect(self.update_status_bar)
            edit_menu.addAction(load_audio_action)

            edit_menu.addSeparator()

            add_firing_action = QAction(QIcon(os.path.join("icons", "plus.png")), "Add Firing", mw)
            add_firing_action.setShortcut("A")
            add_firing_action.triggered.connect(mw.add_firing_btn.click)
            add_firing_action.hovered.connect(self.update_status_bar)
            edit_menu.addAction(add_firing_action)

            delete_firing_action = QAction(QIcon(os.path.join("icons", "delete.png")), "Delete Firing", mw)
            delete_firing_action.setShortcut("D")
            delete_firing_action.triggered.connect(mw.delete_firing_btn.click)
            delete_firing_action.hovered.connect(self.update_status_bar)
            edit_menu.addAction(delete_firing_action)

            edit_menu.addSeparator()

            # Padding submenu
            padding_menu = QMenu("Padding", mw)
            mw.padding_actions = []
            for pad_value in [5, 10, 15, 20, 25, 50]:
                pad_action = QAction(f"{pad_value} seconds", mw)
                pad_action.setCheckable(True)
                pad_action.setChecked(mw.padding == pad_value)
                mw.padding_actions.append(pad_action)
                def make_pad_handler(value=pad_value, action=pad_action):
                    def handler(checked=False):
                        mw.padding = value
                        mw.audio_loader.set_padding(value)
                        for a in mw.padding_actions:
                            a.setChecked(a is action)
                        custom_check = mw.audio_data is not None
                        mw.audio_loader.handle_audio(reload=custom_check)
                    return handler
                pad_action.triggered.connect(make_pad_handler())
                pad_action.hovered.connect(self.update_status_bar)
                padding_menu.addAction(pad_action)
            custom_pad_action = QAction("Custom...", mw)

            def custom_pad_handler():
                text, ok = QInputDialog.getText(
                    mw,
                    "Set Custom Padding Vector",
                    "Enter padding (seconds) before each audio file, separated by commas:\n"
                    "Example: 5,10,5 for 5s before first, 10s before second, 5s before third, etc.",
                    text=",".join(str(v) for v in getattr(mw.audio_loader, "padding_vector", [mw.padding]))
                )
                if ok:
                    try:
                        if "[" in text or "]" in text:
                            text = text.replace("[", "").replace("]", "")
                        padding_vector = [float(v.strip()) for v in text.split(",") if v.strip() != ""]
                        mw.audio_loader.set_padding(padding_vector)
                        mw.padding = padding_vector
                        for a in mw.padding_actions:
                            a.setChecked(False)
                        custom_check = mw.audio_data is not None
                        mw.audio_loader.handle_audio(reload=custom_check)
                    except Exception as e:
                        toast = ToastDialog(f"Invalid input for padding vector: {e}", parent=mw)
                        toast.show()
            custom_pad_action.triggered.connect(custom_pad_handler)
            custom_pad_action.hovered.connect(self.update_status_bar)
            padding_menu.addAction(custom_pad_action)
            edit_menu.addMenu(padding_menu)

        ############################
        # Analysis Menu            #
        ############################

        analysis_menu = None
        for menu in mw.menuBar().findChildren(QMenu):
            if menu.title() == "&Analysis":
                analysis_menu = menu
                break
        if analysis_menu is None:
            analysis_menu = mw.menuBar().addMenu("&Analysis")
        if analysis_menu is not None:
            # Segment Audio
            self.segment_action = QAction("Segment Audio", mw)
            self.segment_action.setShortcut("Ctrl+M")
            def segment_audio():
                if mw.audio_data is None or len(mw.audio_data) == 0:
                    toast = ToastDialog("No audio data available for analysis.", parent=mw)
                    geo = mw.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2500, toast.close)
                    return
                toast = ToastDialog("Loading segments...", parent=mw)
                geo = mw.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(1500, toast.close)
                if mw.analyzer is not None:
                    mw._segments_toast_shown = False
                    try:
                        mw.analyzer.segments_ready.disconnect()
                    except:
                        pass
                    mw.analyzer.segments_ready.connect(mw.firework_show_helper.handle_segments)
                    mw.analyzer.analyze_segments()
            self.segment_action.triggered.connect(segment_audio)
            self.segment_action.hovered.connect(self.update_status_bar)
            analysis_menu.addAction(self.segment_action)

            # Find Interesting Points
            self.interesting_points_action = QAction("Find Interesting Points", mw)
            self.interesting_points_action.setShortcut("Ctrl+I")
            def find_interesting_points():
                if mw.audio_data is None or len(mw.audio_data) == 0:
                    toast = ToastDialog("No audio data available for analysis.", parent=mw)
                    geo = mw.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2500, toast.close)
                    return
                toast = ToastDialog("Loading interesting points...", parent=mw)
                geo = mw.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(1500, toast.close)
                if mw.analyzer is not None:
                    mw._interesting_points_toast_shown = False
                    try:
                        mw.analyzer.interesting_points_ready.disconnect()
                    except:
                        pass
                    mw.analyzer.interesting_points_ready.connect(mw.firework_show_helper.handle_interesting_points)
                    mw.analyzer.analyze_interesting_points()
            self.interesting_points_action.triggered.connect(find_interesting_points)
            self.interesting_points_action.hovered.connect(self.update_status_bar)
            analysis_menu.addAction(self.interesting_points_action)

            # Find Onsets
            self.onsets_action = QAction("Find Onsets", mw)
            self.onsets_action.setShortcut("Ctrl+N")
            def find_onsets():
                if mw.audio_data is None or len(mw.audio_data) == 0:
                    toast = ToastDialog("No audio data available for analysis.", parent=mw)
                    geo = mw.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2500, toast.close)
                    return
                toast = ToastDialog("Loading onsets...", parent=mw)
                geo = mw.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(1500, toast.close)
                if mw.analyzer is not None:
                    mw._onsets_toast_shown = False
                    try:
                        mw.analyzer.onsets_ready.disconnect()
                    except:
                        pass
                    mw.analyzer.onsets_ready.connect(mw.firework_show_helper.handle_onsets)
                    mw.analyzer.analyze_onsets()
            self.onsets_action.triggered.connect(find_onsets)
            self.onsets_action.hovered.connect(self.update_status_bar)
            analysis_menu.addAction(self.onsets_action)

            # Find Local Maxima
            self.maxima_action = QAction("Find Local Maxima", mw)
            self.maxima_action.setShortcut("Ctrl+X")
            def find_local_maxima():
                if mw.audio_data is None or len(mw.audio_data) == 0:
                    toast = ToastDialog("No audio data available for analysis.", parent=mw)
                    geo = mw.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2500, toast.close)
                    return
                toast = ToastDialog("Loading local maxima...", parent=mw)
                geo = mw.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(1500, toast.close)
                if mw.analyzer is not None:
                    mw._peaks_toast_shown = False
                    try:
                        mw.analyzer.peaks_ready.disconnect()
                    except:
                        pass
                    mw.analyzer.peaks_ready.connect(mw.firework_show_helper.handle_peaks)
                    mw.analyzer.analyze_maxima()
            self.maxima_action.triggered.connect(find_local_maxima)
            self.maxima_action.hovered.connect(self.update_status_bar)
            analysis_menu.addAction(self.maxima_action)

            analysis_menu.addSeparator()

            # Apply Filter
            apply_filter_action = QAction("Apply Filter...", mw)
            apply_filter_action.setShortcut("Ctrl+F")
            def open_filter_dialog():
                dialog = FilterDialog(mw)
                if dialog.exec():
                    filter_type, order, cutoff = dialog.get_values()
                    mw.filter_type = filter_type
                    mw.order = order
                    mw.cutoff = cutoff
                    mw.filter_kwargs = {"order": order, "cutoff": cutoff}
                    if mw.audio_data is not None and mw.sr is not None:
                        try:
                            if mw.filter is None or not hasattr(mw.filter, "apply"):
                                mw.filter = AudioFilter(mw.sr, mw.audio_data)
                            elif mw.filter.original_audio is None:
                                # Ensure original audio is preserved
                                mw.filter.original_audio = mw.audio_data.copy()
                            if filter_type.lower() in ["lowpass", "highpass", "bandpass"]:
                                kwargs = {"sr": mw.sr, "order": order}
                                if filter_type.lower() == "bandpass":
                                    lowcut, highcut = cutoff if isinstance(cutoff, (tuple, list)) and len(cutoff) == 2 else (1000.0, 5000.0)
                                    kwargs["lowcut"] = lowcut
                                    kwargs["highcut"] = highcut
                                else:
                                    kwargs["cutoff"] = cutoff
                                filtered = mw.filter.apply(mw.audio_data, filter_type.lower(), **kwargs)
                                mw.audio_data = filtered
                                mw.firework_show_helper.plot_waveform()
                                mw.firework_show_helper.plot_spectrogram()
                                toast = ToastDialog(f"Applied {filter_type} filter!", parent=mw)
                                geo = mw.geometry()
                                x = geo.x() + geo.width() - toast.width() - 40
                                y = geo.y() + geo.height() - toast.height() - 40
                                toast.move(x, y)
                                toast.show()
                                QTimer.singleShot(2000, toast.close)
                            else:
                                toast = ToastDialog(f"Filter type '{filter_type}' is not supported.", parent=mw)
                                toast.show()
                                QTimer.singleShot(2500, toast.close)
                        except Exception as e:
                            toast = ToastDialog(f"Filter error: {e}", parent=mw)
                            toast.show()
                            QTimer.singleShot(2500, toast.close)
            apply_filter_action.triggered.connect(open_filter_dialog)
            apply_filter_action.hovered.connect(self.update_status_bar)
            analysis_menu.addAction(apply_filter_action)

            ############################
            # Help Menu                #
            ############################
            
            help_menu = mw.menuBar().addMenu("&Help")
            if help_menu is not None:
                help_action = QAction("How to Use Firework Studio", mw)
                help_action.setShortcut("F1")
                def show_help_dialog():
                    help_text = (
                    "<b>How to Load Multiple Audio Files:</b><br>"
                    "Click the <b>Load Audio</b> button or use <b>Ctrl+L</b> to select and load audio files.<br>"
                    "You can load more than one file, and it concatenates them in the same order they are displayed in the file dialog window.<br><br>"
                    "<b>Changing Number of Firings and Pattern:</b><br>"
                    "Use the <b>Up/Down arrow keys</b> to change the number of fireworks fired at each time.<br>"
                    "Use the <b>Left/Right arrow keys</b> to change the firework pattern.<br><br>"
                    "<b>Saving and Loading a Show:</b><br>"
                    "Click the <b>Save</b> button or use <b>Ctrl+S</b> to save your show.<br>"
                    "Click the <b>Load</b> button or use <b>Ctrl+O</b> to load a previously saved show.<br><br>"
                    "<b>Preview Widget:</b><br>"
                    "The preview widget lets you select a region of the audio by clicking and dragging.<br>"
                    "Right-click on the preview widget to access context menu options for firings.<br>"
                    )
                    dialog = ToastDialog(help_text, parent=mw)
                    dialog.setWindowTitle("Firework Studio Help")
                    dialog.setMinimumWidth(500)
                    dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
                    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
                    # Add a close button to the dialog
                    layout = dialog.layout() if dialog.layout() else QVBoxLayout(dialog)
                    close_btn = QPushButton("Close", dialog)
                    close_btn.clicked.connect(dialog.close)
                    layout.addWidget(close_btn)
                    dialog.setLayout(layout)
                    dialog.show()
                help_action.triggered.connect(show_help_dialog)
                help_action.hovered.connect(self.update_status_bar)
                help_menu.addAction(help_action)
