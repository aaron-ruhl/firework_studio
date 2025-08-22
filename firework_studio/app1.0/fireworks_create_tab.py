from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QSpinBox, QComboBox, QLineEdit
)

class CreateTabHelper:
    def __init__(self, main_window):
        self.main_window = main_window
        self.create_tab_widget = QWidget()

        # Create a scroll area for the tab content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QWidget {
            background-color: #23242b;
            color: #ffd700;
            font-size: 15px;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QGroupBox {
            background-color: #181a20;
            border: 2px solid #ffd700;
            border-radius: 8px;
            color: #ffd700;
            font-size: 16px;
            font-weight: bold;
            margin-top: 12px;
            margin-bottom: 12px;
            padding: 8px 12px;
            }
            QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: #ffd700;
            font-size: 16px;
            font-weight: bold;
            }
            QLabel {
            color: #ffd700;
            font-size: 15px;
            font-weight: 500;
            padding: 4px 0;
            }
            QComboBox, QSpinBox {
            background-color: #23242b;
            color: #ffd700;
            border: 2px solid #ffd700;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            min-width: 60px;
            min-height: 32px;
            padding: 4px 12px;
            margin: 4px 0;
            }
            QPushButton {
            background-color: #ffd700;
            color: #23242b;
            border: 2px solid #ffd700;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            min-width: 80px;
            min-height: 32px;
            margin: 6px 0;
            }
            QPushButton:hover {
            background-color: #fffbe6;
            color: #23242b;
            border: 2px solid #ffd700;
            }
            QMenu {
            background-color: #23242b;
            color: #ffd700;
            border: 2px solid #ffd700;
            border-radius: 8px;
            font-size: 15px;
            padding: 8px 0px;
            }
            QTabWidget::pane {
            border: 2px solid #ffd700;
            background: #23242b;
            }
            QTabBar::tab {
            background: #181a20;
            color: #ffd700;
            border: 2px solid #ffd700;
            border-radius: 6px;
            min-width: 140px;
            min-height: 36px;
            font-size: 15px;
            font-weight: bold;
            margin: 4px;
            }
            QTabBar::tab:selected {
            background: #ffd700;
            color: #23242b;
            border: 2px solid #ffd700;
            }
            QTabBar::tab:hover {
            background-color: #fffbe6;
            color: #23242b;
            }
        """)

        # Create the actual content widget and layout
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        content_widget.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(QLabel("Lay down firing..."))

        analysis_label = QLabel("Analysis Settings")
        analysis_label.setStyleSheet("""
            QLabel {
            color: #ffd700;
            font-size: 20px;
            font-weight: bold;
            letter-spacing: 1px;
            padding: 8px 0 12px 0;
            border-bottom: 2px solid #ffd700;
            margin-bottom: 12px;
            background: transparent;
            }
        """)
        analysis_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(analysis_label)
        analysis_section = QHBoxLayout()
        analysis_section.setSpacing(12)
        analysis_section.setContentsMargins(0, 0, 0, 0)

        # --- Segment Settings ---
        segment_group = QGroupBox("Segment Settings")
        segment_layout = QVBoxLayout()
        self.min_segments_spin = QSpinBox()
        self.min_segments_spin.setRange(1, 50)
        self.min_segments_spin.setValue(2)
        self.min_segments_spin.setPrefix("Min: ")
        self.min_segments_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(self.min_segments_spin)
        self.max_segments_spin = QSpinBox()
        self.max_segments_spin.setRange(2, 50)
        self.max_segments_spin.setValue(19)
        self.max_segments_spin.setPrefix("Max: ")
        self.max_segments_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(self.max_segments_spin)
        self.n_mfcc_spin = QSpinBox()
        self.n_mfcc_spin.setRange(1, 40)
        self.n_mfcc_spin.setValue(13)
        self.n_mfcc_spin.setPrefix("MFCC: ")
        self.n_mfcc_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(self.n_mfcc_spin)
        self.dct_type_spin = QSpinBox()
        self.dct_type_spin.setRange(1, 4)
        self.dct_type_spin.setValue(2)
        self.dct_type_spin.setPrefix("DCT: ")
        self.dct_type_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(self.dct_type_spin)
        self.n_fft_spin = QSpinBox()
        self.n_fft_spin.setRange(256, 8192)
        self.n_fft_spin.setValue(2048)
        self.n_fft_spin.setPrefix("FFT: ")
        self.n_fft_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(self.n_fft_spin)
        self.hop_length_segments_spin = QSpinBox()
        self.hop_length_segments_spin.setRange(64, 4096)
        self.hop_length_segments_spin.setValue(512)
        self.hop_length_segments_spin.setPrefix("Hop: ")
        self.hop_length_segments_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(self.hop_length_segments_spin)
        segment_group.setLayout(segment_layout)
        segment_group.setMinimumWidth(220)
        segment_group.setMaximumWidth(260)
        analysis_section.addWidget(segment_group)

        # --- Onset Settings ---
        onset_group = QGroupBox("Onset Settings")
        onset_layout = QVBoxLayout()
        self.min_onsets_spin = QSpinBox()
        self.min_onsets_spin.setRange(1, 100)
        self.min_onsets_spin.setValue(5)
        self.min_onsets_spin.setPrefix("Min: ")
        self.min_onsets_spin.setStyleSheet("font-size: 10px;")
        onset_layout.addWidget(self.min_onsets_spin)
        self.max_onsets_spin = QSpinBox()
        self.max_onsets_spin.setRange(1, 100)
        self.max_onsets_spin.setValue(20)
        self.max_onsets_spin.setPrefix("Max: ")
        self.max_onsets_spin.setStyleSheet("font-size: 10px;")
        onset_layout.addWidget(self.max_onsets_spin)
        self.hop_length_onsets_spin = QSpinBox()
        self.hop_length_onsets_spin.setRange(64, 4096)
        self.hop_length_onsets_spin.setValue(512)
        self.hop_length_onsets_spin.setPrefix("Hop: ")
        self.hop_length_onsets_spin.setStyleSheet("font-size: 10px;")
        onset_layout.addWidget(self.hop_length_onsets_spin)
        self.backtrack_box = QComboBox()
        self.backtrack_box.addItems(["True", "False"])
        self.backtrack_box.setCurrentIndex(0)
        self.backtrack_box.setEditable(False)
        self.backtrack_box.setMinimumWidth(80)
        self.backtrack_box.setMaximumWidth(120)
        self.backtrack_box.setStyleSheet("font-size: 10px;")
        backtrack_label = QLabel(
            "<b>Backtrack:</b><br>"
            "This is primarily useful when using onsets as slice points for segmentation.<br>"
            "If enabled, detected onsets are shifted to the nearest preceding peak in the signal."
        )
        backtrack_label.setWordWrap(True)
        backtrack_label.setStyleSheet("font-size: 11px; color: #ffd700; padding: 2px 0;")
        backtrack_label.setMinimumHeight(9)
        onset_layout.addWidget(backtrack_label)
        onset_layout.addWidget(self.backtrack_box)
        self.normalize_box = QComboBox()
        self.normalize_box.addItems(["True", "False"])
        self.normalize_box.setCurrentIndex(1)
        self.normalize_box.setEditable(False)
        self.normalize_box.setMinimumWidth(80)
        self.normalize_box.setMaximumWidth(120)
        self.normalize_box.setStyleSheet("font-size: 10px;")
        onset_layout.addWidget(QLabel("Normalize:"))
        onset_layout.addWidget(self.normalize_box)
        onset_group.setLayout(onset_layout)
        onset_group.setMinimumWidth(220)
        onset_group.setMaximumWidth(260)
        analysis_section.addWidget(onset_group)

        # --- Interesting Points Settings ---
        points_group = QGroupBox("Interesting Points Settings")
        points_layout = QVBoxLayout()
        self.min_points_spin = QSpinBox()
        self.min_points_spin.setRange(1, 100)
        self.min_points_spin.setValue(5)
        self.min_points_spin.setPrefix("Min: ")
        self.min_points_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.min_points_spin)
        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(1, 100)
        self.max_points_spin.setValue(20)
        self.max_points_spin.setPrefix("Max: ")
        self.max_points_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.max_points_spin)
        self.pre_max_spin = QSpinBox()
        self.pre_max_spin.setRange(0, 20)
        self.pre_max_spin.setValue(3)
        self.pre_max_spin.setPrefix("PreMax: ")
        self.pre_max_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.pre_max_spin)
        self.post_max_spin = QSpinBox()
        self.post_max_spin.setRange(0, 20)
        self.post_max_spin.setValue(3)
        self.post_max_spin.setPrefix("PostMax: ")
        self.post_max_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.post_max_spin)
        self.pre_avg_distance_spin = QSpinBox()
        self.pre_avg_distance_spin.setRange(0, 20)
        self.pre_avg_distance_spin.setValue(3)
        self.pre_avg_distance_spin.setPrefix("PreAvgDist: ")
        self.pre_avg_distance_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.pre_avg_distance_spin)
        self.post_avg_distance_spin = QSpinBox()
        self.post_avg_distance_spin.setRange(0, 20)
        self.post_avg_distance_spin.setValue(5)
        self.post_avg_distance_spin.setPrefix("PostAvgDist: ")
        self.post_avg_distance_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.post_avg_distance_spin)
        self.delta_spin = QSpinBox()
        self.delta_spin.setRange(0, 100)
        self.delta_spin.setValue(5)
        self.delta_spin.setPrefix("Delta x0.1: ")
        self.delta_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.delta_spin)
        self.moving_avg_wait_spin = QSpinBox()
        self.moving_avg_wait_spin.setRange(0, 20)
        self.moving_avg_wait_spin.setValue(5)
        self.moving_avg_wait_spin.setPrefix("MA Wait: ")
        self.moving_avg_wait_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.moving_avg_wait_spin)
        points_group.setLayout(points_layout)
        points_group.setMinimumWidth(220)
        points_group.setMaximumWidth(260)
        analysis_section.addWidget(points_group)

        # --- Peak Settings ---
        peak_group = QGroupBox("Peak Settings")
        peak_layout = QVBoxLayout()
        self.min_peaks_spin = QSpinBox()
        self.min_peaks_spin.setRange(1, 100)
        self.min_peaks_spin.setValue(1)
        self.min_peaks_spin.setPrefix("Min: ")
        self.min_peaks_spin.setStyleSheet("font-size: 10px;")
        peak_layout.addWidget(self.min_peaks_spin)
        self.max_peaks_spin = QSpinBox()
        self.max_peaks_spin.setRange(1, 1000)
        self.max_peaks_spin.setValue(3)
        self.max_peaks_spin.setPrefix("Max: ")
        self.max_peaks_spin.setStyleSheet("font-size: 10px;")
        peak_layout.addWidget(self.max_peaks_spin)
        self.scoring_box = QComboBox()
        self.scoring_box.addItems(["squared", "absolute", "relative", "sharp", "custom"])
        self.scoring_box.setCurrentIndex(0)
        self.scoring_box.setMinimumWidth(100)
        self.scoring_box.setMaximumWidth(140)
        self.scoring_box.setStyleSheet("font-size: 10px;")
        label = QLabel(
            "<b>Scoring:</b><br>"
            "This enables the user to set the scoring method used to determine which peaks to keep.<br>"
            "<b>Current options:</b> <code>absolute</code>, <code>relative</code>, <code>sharp</code>, <code>custom</code>."
        )
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 11px; color: #ffd700; padding: 2px 0;")
        label.setMinimumHeight(9)
        peak_layout.addWidget(label)
        peak_layout.addWidget(self.scoring_box)
        self.custom_function_edit = QLineEdit()
        self.custom_function_edit.setPlaceholderText("custom_scoring_method(audio_data_region, zero_crossings)")
        self.custom_function_edit.setStyleSheet("font-size: 10px;")
        label = QLabel(
            "<b>Custom Function:</b><br>"
            "Define a lambda function for custom peak scoring.<br>"
            "Example: <br><code>lambda audio_data_region, zero_crossings: np.abs(audio_data_region[zero_crossings])</code><br>"
            "<b>Arguments:</b>"
            "<ul>"
            "<li><b>audio_data_region</b>: The audio currently selected by the user.</li>"
            "<li><b>zero_crossings</b>: Locations of detected zero crossings (all found peaks).</li>"
            "</ul>"
        )
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 11px; color: #ffd700; padding: 2px 0;")
        label.setMinimumHeight(9)
        peak_layout.addWidget(label)
        peak_layout.addWidget(self.custom_function_edit)
        peak_group.setLayout(peak_layout)
        peak_group.setMinimumWidth(280)
        peak_group.setMaximumWidth(400)
        analysis_section.addWidget(peak_group, stretch=2)

        # Connect signals to slots (move these inside __init__)
        for spin in [self.n_mfcc_spin, self.min_segments_spin, self.dct_type_spin, self.n_fft_spin, self.hop_length_segments_spin]:
            spin.valueChanged.connect(self.update_segment_settings)
        self.min_segments_spin.valueChanged.connect(self.update_segment_settings)
        self.max_segments_spin.valueChanged.connect(self.update_segment_settings)

        for spin in [self.min_onsets_spin, self.max_onsets_spin, self.hop_length_onsets_spin]:
            spin.valueChanged.connect(self.update_onset_settings)
        self.backtrack_box.currentIndexChanged.connect(self.update_onset_settings)
        self.normalize_box.currentIndexChanged.connect(self.update_onset_settings)

        for spin in [self.min_points_spin, self.max_points_spin, self.pre_max_spin, self.post_max_spin, self.pre_avg_distance_spin, self.post_avg_distance_spin, self.delta_spin, self.moving_avg_wait_spin]:
            spin.valueChanged.connect(self.update_points_settings)

        for spin in [self.min_peaks_spin, self.max_peaks_spin]:
            spin.valueChanged.connect(self.update_peak_settings)

        self.scoring_box.currentIndexChanged.connect(self.update_peak_settings)
        self.custom_function_edit.textChanged.connect(self.update_peak_settings)

        main_layout.addLayout(analysis_section)

        content_widget.setLayout(main_layout)
        scroll_area.setWidget(content_widget)
        scroll_area.setContentsMargins(0, 0, 0, 0)

        create_tab_widget_layout = QVBoxLayout(self.create_tab_widget)
        create_tab_widget_layout.setContentsMargins(0, 8, 0, 8)
        create_tab_widget_layout.addWidget(scroll_area)
        self.create_tab_widget.setLayout(create_tab_widget_layout)
        self.create_tab_widget.setContentsMargins(0, 0, 0, 0)

    # --- Connect fields to analyzer setters ---
    def update_segment_settings(self):
        if self.main_window.analyzer is not None:
            self.main_window.analyzer.set_segment_settings(
                n_mfcc=self.n_mfcc_spin.value(),
                min_segments=self.min_segments_spin.value(),
                max_segments=self.max_segments_spin.value(),
                dct_type=self.dct_type_spin.value(),
                n_fft=self.n_fft_spin.value(),
                hop_length_segments=self.hop_length_segments_spin.value()
            )

    def update_onset_settings(self):
        if self.main_window.analyzer is not None:
            self.main_window.analyzer.set_onset_settings(
                min_onsets=self.min_onsets_spin.value(),
                max_onsets=self.max_onsets_spin.value(),
                hop_length_onsets=self.hop_length_onsets_spin.value(),
                backtrack=self.backtrack_box.currentText() == "True",
                normalize=self.normalize_box.currentText() == "True"
            )

    def update_points_settings(self):
        if self.main_window.analyzer is not None:
            self.main_window.analyzer.set_interesting_points_settings(
                min_points=self.min_points_spin.value(),
                max_points=self.max_points_spin.value(),
                pre_max=self.pre_max_spin.value(),
                post_max=self.post_max_spin.value(),
                pre_avg_distance=self.pre_avg_distance_spin.value(),
                post_avg_distance=self.post_avg_distance_spin.value(),
                delta=self.delta_spin.value() * 0.1,
                moving_avg_wait=self.moving_avg_wait_spin.value()
            )

    def update_peak_settings(self):
        custom_func = None
        text = self.custom_function_edit.text().strip()
        if text:
            try:
                if text.startswith("lambda"):
                    custom_func = eval(text, {"__builtins__": {}}, {})
            except Exception:
                custom_func = None
        if self.main_window.analyzer is not None:
            self.main_window.analyzer.set_peak_settings(
                min_peaks=self.min_peaks_spin.value(),
                max_peaks=self.max_peaks_spin.value(),
                scoring=self.scoring_box.currentText(),
                custom_scoring_method=custom_func
            )

    