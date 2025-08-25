from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QSpinBox, QComboBox, QLineEdit, QDialog, QPushButton
)

class SettingsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Firework Studio Settings")
        self.setModal(True)
        self.setMinimumSize(1100, 700)
        self.resize(1100, 700)
        
        # Apply the same dark styling as the main window
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffd700;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffd700;
            }
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #1e1e1e;
            }
            QGroupBox {
                background-color: #23242b;
                border: 1px solid #444657;
                border-radius: 6px;
                color: #ffd700;
                font-size: 13px;
                font-weight: bold;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
                color: #ffd700;
                font-size: 13px;
                font-weight: bold;
                background-color: #1e1e1e;
            }
            QSpinBox {
                background-color: #23242b;
                color: #ffd700;
                border: 1px solid #444657;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                min-width: 40px;
                max-width: 120px;
                padding: 2px 8px;
                margin: 2px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #31323a;
                border: 1px solid #444657;
                border-radius: 2px;
                width: 16px;
                height: 14px;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 10px;
                height: 10px;
                color: #ffd700;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #ffd700;
                border: 1.2px solid #ffd700;
            }
            QSpinBox:focus {
                border: 1.2px solid #ffd700;
                color: #ffd700;
            }
            QComboBox {
                background: #23242b;
                color: #ffd700;
                border: 1px solid #444657;
                font-size: 12px;
                border-radius: 4px;
                padding: 3px 16px 3px 6px;
                min-width: 40px;
                max-width: 120px;
                margin: 2px;
            }
            QComboBox:hover, QComboBox:focus {
                background: #31323a;
                color: #ffd700;
                border: 1.2px solid #ffd700;
            }
            QComboBox::drop-down {
                background: #23242b;
                border-left: 1px solid #444657;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 16px;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
                color: #ffd700;
            }
            QComboBox QAbstractItemView {
                background: #23242b;
                border: 1px solid #444657;
                color: #ffd700;
                selection-background-color: #31323a;
                selection-color: #ffd700;
                outline: none;
            }
            QLineEdit {
                background-color: #23242b;
                color: #ffd700;
                border: 1px solid #444657;
                border-radius: 4px;
                font-size: 12px;
                padding: 4px 8px;
                margin: 2px;
            }
            QLineEdit:focus {
                border: 1.2px solid #ffd700;
            }
            QLabel {
                background-color: transparent;
                color: #ffd700;
            }
            QPushButton {
                background-color: #49505a;
                color: #ffd700;
                border: 1px solid #444657;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 500;
                min-width: 80px;
                min-height: 28px;
                padding: 4px 12px;
                margin: 4px;
            }
            QPushButton:hover {
                background-color: #606874;
                border: 1.2px solid #ffd700;
            }
            QPushButton:pressed {
                background-color: #353a40;
                border: 1.2px solid #ffd700;
            }
        """)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        
        # Create scroll area for the settings content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #23242b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #49505a;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #606874;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Create the actual content widget and layout
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #1e1e1e;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

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
        content_layout.addWidget(analysis_label)
        
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
        self.min_onsets_spin.setRange(1, 10)
        self.min_onsets_spin.setValue(5)
        self.min_onsets_spin.setPrefix("Min: ")
        self.min_onsets_spin.setStyleSheet("font-size: 10px;")
        onset_layout.addWidget(self.min_onsets_spin)
        self.max_onsets_spin = QSpinBox()
        self.max_onsets_spin.setRange(1, 10)
        self.max_onsets_spin.setValue(10)
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
        self.min_points_spin.setRange(1, 10)
        self.min_points_spin.setValue(5)
        self.min_points_spin.setPrefix("Min: ")
        self.min_points_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.min_points_spin)
        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(1, 10)
        self.max_points_spin.setValue(20)
        self.max_points_spin.setPrefix("Max: ")
        self.max_points_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(self.max_points_spin)
        self.pre_max_spin = QSpinBox()
        self.pre_max_spin.setRange(0, 20)
        self.pre_max_spin.setValue(10)
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
        self.min_peaks_spin.setRange(1, 10)
        self.min_peaks_spin.setValue(1)
        self.min_peaks_spin.setPrefix("Min: ")
        self.min_peaks_spin.setStyleSheet("font-size: 10px;")
        peak_layout.addWidget(self.min_peaks_spin)
        self.max_peaks_spin = QSpinBox()
        self.max_peaks_spin.setRange(1, 10)
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

        content_layout.addLayout(analysis_section)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        # Add the scroll area to the main layout
        main_layout.addWidget(scroll_area)
        
        # Create button layout for OK/Cancel buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Connect all the signal handlers
        self.connect_signals()
        
    def connect_signals(self):
        # Connect signals to slots for all settings
        for spin in [self.n_mfcc_spin, self.min_segments_spin, self.max_segments_spin, 
                     self.dct_type_spin, self.n_fft_spin, self.hop_length_segments_spin]:
            spin.valueChanged.connect(self.update_segment_settings)

        for spin in [self.min_onsets_spin, self.max_onsets_spin, self.hop_length_onsets_spin]:
            spin.valueChanged.connect(self.update_onset_settings)
        self.backtrack_box.currentIndexChanged.connect(self.update_onset_settings)
        self.normalize_box.currentIndexChanged.connect(self.update_onset_settings)

        for spin in [self.min_points_spin, self.max_points_spin, self.pre_max_spin, 
                     self.post_max_spin, self.pre_avg_distance_spin, self.post_avg_distance_spin, 
                     self.delta_spin, self.moving_avg_wait_spin]:
            spin.valueChanged.connect(self.update_points_settings)

        for spin in [self.min_peaks_spin, self.max_peaks_spin]:
            spin.valueChanged.connect(self.update_peak_settings)

        self.scoring_box.currentIndexChanged.connect(self.update_peak_settings)
        self.custom_function_edit.textChanged.connect(self.update_peak_settings)

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

    def get_current_settings(self):
        """Get all current settings as a dictionary"""
        custom_func = None
        text = self.custom_function_edit.text().strip()
        if text:
            try:
                if text.startswith("lambda"):
                    custom_func = eval(text, {"__builtins__": {}}, {})
            except Exception:
                custom_func = None
        
        return {
            'segment': {
                'n_mfcc': self.n_mfcc_spin.value(),
                'min_segments': self.min_segments_spin.value(),
                'max_segments': self.max_segments_spin.value(),
                'dct_type': self.dct_type_spin.value(),
                'n_fft': self.n_fft_spin.value(),
                'hop_length_segments': self.hop_length_segments_spin.value()
            },
            'onset': {
                'min_onsets': self.min_onsets_spin.value(),
                'max_onsets': self.max_onsets_spin.value(),
                'hop_length_onsets': self.hop_length_onsets_spin.value(),
                'backtrack': self.backtrack_box.currentText() == "True",
                'normalize': self.normalize_box.currentText() == "True"
            },
            'points': {
                'min_points': self.min_points_spin.value(),
                'max_points': self.max_points_spin.value(),
                'pre_max': self.pre_max_spin.value(),
                'post_max': self.post_max_spin.value(),
                'pre_avg_distance': self.pre_avg_distance_spin.value(),
                'post_avg_distance': self.post_avg_distance_spin.value(),
                'delta': self.delta_spin.value() * 0.1,
                'moving_avg_wait': self.moving_avg_wait_spin.value()
            },
            'peaks': {
                'min_peaks': self.min_peaks_spin.value(),
                'max_peaks': self.max_peaks_spin.value(),
                'scoring': self.scoring_box.currentText(),
                'custom_scoring_method': custom_func
            }
        }

    def apply_all_settings_to_analyzer(self):
        """Apply all current dialog settings to the analyzer"""
        if self.main_window.analyzer is not None:
            # Apply all settings at once
            self.update_segment_settings()
            self.update_onset_settings()
            self.update_points_settings()
            self.update_peak_settings()

    def load_settings(self, settings_dict):
        """Load settings from a dictionary into the dialog controls"""
        try:
            # Load segment settings
            if 'segment' in settings_dict:
                seg = settings_dict['segment']
                self.n_mfcc_spin.setValue(seg.get('n_mfcc', 13))
                self.min_segments_spin.setValue(seg.get('min_segments', 2))
                self.max_segments_spin.setValue(seg.get('max_segments', 19))
                self.dct_type_spin.setValue(seg.get('dct_type', 2))
                self.n_fft_spin.setValue(seg.get('n_fft', 2048))
                self.hop_length_segments_spin.setValue(seg.get('hop_length_segments', 512))
            
            # Load onset settings
            if 'onset' in settings_dict:
                onset = settings_dict['onset']
                self.min_onsets_spin.setValue(onset.get('min_onsets', 5))
                self.max_onsets_spin.setValue(onset.get('max_onsets', 20))
                self.hop_length_onsets_spin.setValue(onset.get('hop_length_onsets', 512))
                self.backtrack_box.setCurrentText("True" if onset.get('backtrack', True) else "False")
                self.normalize_box.setCurrentText("True" if onset.get('normalize', False) else "False")
            
            # Load points settings
            if 'points' in settings_dict:
                points = settings_dict['points']
                self.min_points_spin.setValue(points.get('min_points', 5))
                self.max_points_spin.setValue(points.get('max_points', 20))
                self.pre_max_spin.setValue(points.get('pre_max', 3))
                self.post_max_spin.setValue(points.get('post_max', 3))
                self.pre_avg_distance_spin.setValue(points.get('pre_avg_distance', 3))
                self.post_avg_distance_spin.setValue(points.get('post_avg_distance', 5))
                # Note: delta is stored as 0.5 but display shows delta * 10
                self.delta_spin.setValue(int(points.get('delta', 0.5) * 10))
                self.moving_avg_wait_spin.setValue(points.get('moving_avg_wait', 5))
            
            # Load peaks settings
            if 'peaks' in settings_dict:
                peaks = settings_dict['peaks']
                self.min_peaks_spin.setValue(peaks.get('min_peaks', 1))
                self.max_peaks_spin.setValue(peaks.get('max_peaks', 3))
                
                # Set scoring method
                scoring = peaks.get('scoring', 'squared')
                index = self.scoring_box.findText(scoring)
                if index >= 0:
                    self.scoring_box.setCurrentIndex(index)
                
                # Set custom function if it exists
                custom_func = peaks.get('custom_scoring_method')
                if custom_func is not None:
                    # Convert function back to string representation if possible
                    # This is a simplified approach - in practice you might want to store the string
                    self.custom_function_edit.setText("")
                else:
                    self.custom_function_edit.setText("")
                    
        except Exception as e:
            print(f"Error loading settings: {e}")
            # If loading fails, continue with default values


class SettingsManager:
    """Singleton class to manage settings across the application"""
    _instance = None
    _settings_dialog = None
    _current_settings = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_settings = cls._instance._get_default_settings()
        return cls._instance
    
    def set_settings_dialog(self, dialog):
        """Set the current settings dialog instance"""
        self._settings_dialog = dialog
        # Load previous settings into the dialog if they exist
        if self._current_settings is not None:
            dialog.load_settings(self._current_settings)
    
    def clear_settings_dialog(self):
        """Clear the settings dialog reference"""
        self._settings_dialog = None
    
    def save_current_settings(self):
        """Save the current settings from the active dialog"""
        if self._settings_dialog is not None:
            self._current_settings = self._settings_dialog.get_current_settings()
    
    def get_current_settings(self):
        """Get current settings from the active dialog or stored settings"""
        if self._settings_dialog is not None:
            # Get live settings from dialog and store them
            self._current_settings = self._settings_dialog.get_current_settings()
            return self._current_settings
        elif self._current_settings is not None:
            # Return previously stored settings
            return self._current_settings
        
        # Return default settings if nothing is available
        return self._get_default_settings()
    
    def _get_default_settings(self):
        """Get default settings"""
        return {
            'segment': {
                'n_mfcc': 13,
                'min_segments': 2,
                'max_segments': 19,
                'dct_type': 2,
                'n_fft': 2048,
                'hop_length_segments': 512
            },
            'onset': {
                'min_onsets': 5,
                'max_onsets': 10,
                'hop_length_onsets': 512,
                'backtrack': True,
                'normalize': False
            },
            'points': {
                'min_points': 5,
                'max_points': 10,
                'pre_max': 3,
                'post_max': 3,
                'pre_avg_distance': 3,
                'post_avg_distance': 5,
                'delta': 0.5,
                'moving_avg_wait': 5
            },
            'peaks': {
                'min_peaks': 1,
                'max_peaks': 10,
                'scoring': 'squared',
                'custom_scoring_method': None
            }
        }
    
    def apply_settings_to_analyzer(self, analyzer):
        """Apply current settings to the given analyzer"""
        if analyzer is None:
            return
            
        settings = self.get_current_settings()
        
        # Apply segment settings
        analyzer.set_segment_settings(**settings['segment'])
        
        # Apply onset settings  
        analyzer.set_onset_settings(**settings['onset'])
        
        # Apply interesting points settings
        analyzer.set_interesting_points_settings(**settings['points'])
        
        # Apply peak settings
        analyzer.set_peak_settings(**settings['peaks'])
    
    def get_min_onsets(self):
        """Get current minimum onsets value"""
        if self._settings_dialog is not None:
            return self._settings_dialog.min_onsets_spin.value()
        else:
            settings = self.get_current_settings()
            return settings['onset']['min_onsets']
    
    def get_max_onsets(self):
        """Get current maximum onsets value"""
        if self._settings_dialog is not None:
            return self._settings_dialog.max_onsets_spin.value()
        else:
            settings = self.get_current_settings()
            return settings['onset']['max_onsets']
    
    def set_min_onsets(self, value):
        """Set minimum onsets value"""
        if self._settings_dialog is not None:
            self._settings_dialog.min_onsets_spin.setValue(value)
            # Don't automatically set max_onsets - let user control that separately
        else:
            if self._current_settings is None:
                self._current_settings = self._get_default_settings()
            self._current_settings['onset']['min_onsets'] = value
            # Also update max_onsets if it's less than min_onsets to maintain validity
            if self._current_settings['onset']['max_onsets'] < value:
                self._current_settings['onset']['max_onsets'] = value
    
    def set_min_onsets_and_apply(self, value, analyzer=None):
        """Set minimum onsets value and apply to analyzer if available"""
        self.set_min_onsets(value)
        if analyzer is not None:
            settings = self.get_current_settings()
            analyzer.set_onset_settings(**settings['onset'])
    
    def set_max_onsets(self, value):
        """Set maximum onsets value"""
        if self._settings_dialog is not None:
            self._settings_dialog.max_onsets_spin.setValue(value)
        else:
            if self._current_settings is None:
                self._current_settings = self._get_default_settings()
            self._current_settings['onset']['max_onsets'] = value
            # Also update min_onsets if it's greater than max_onsets to maintain validity
            if self._current_settings['onset']['min_onsets'] > value:
                self._current_settings['onset']['min_onsets'] = value
    
    def set_max_onsets_and_apply(self, value, analyzer=None):
        """Set maximum onsets value and apply to analyzer if available"""
        self.set_max_onsets(value)
        if analyzer is not None:
            settings = self.get_current_settings()
            analyzer.set_onset_settings(**settings['onset'])
    
    def get_min_points(self):
        """Get current minimum interesting points value"""
        if self._settings_dialog is not None:
            return self._settings_dialog.min_points_spin.value()
        else:
            settings = self.get_current_settings()
            return settings['points']['min_points']
    
    def get_max_points(self):
        """Get current maximum interesting points value"""
        if self._settings_dialog is not None:
            return self._settings_dialog.max_points_spin.value()
        else:
            settings = self.get_current_settings()
            return settings['points']['max_points']
    
    def set_min_points(self, value):
        """Set minimum interesting points value"""
        if self._settings_dialog is not None:
            self._settings_dialog.min_points_spin.setValue(value)
            # Don't automatically set max_points - let user control that separately
        else:
            if self._current_settings is None:
                self._current_settings = self._get_default_settings()
            self._current_settings['points']['min_points'] = value
            # Also update max_points if it's less than min_points to maintain validity
            if self._current_settings['points']['max_points'] < value:
                self._current_settings['points']['max_points'] = value
    
    def set_min_points_and_apply(self, value, analyzer=None):
        """Set minimum interesting points value and apply to analyzer if available"""
        self.set_min_points(value)
        if analyzer is not None:
            settings = self.get_current_settings()
            analyzer.set_interesting_points_settings(**settings['points'])
    
    def set_max_points(self, value):
        """Set maximum interesting points value"""
        if self._settings_dialog is not None:
            self._settings_dialog.max_points_spin.setValue(value)
        else:
            if self._current_settings is None:
                self._current_settings = self._get_default_settings()
            self._current_settings['points']['max_points'] = value
            # Also update min_points if it's greater than max_points to maintain validity
            if self._current_settings['points']['min_points'] > value:
                self._current_settings['points']['min_points'] = value
    
    def set_max_points_and_apply(self, value, analyzer=None):
        """Set maximum interesting points value and apply to analyzer if available"""
        self.set_max_points(value)
        if analyzer is not None:
            settings = self.get_current_settings()
            analyzer.set_interesting_points_settings(**settings['points'])
    
    def get_max_peaks(self):
        """Get current maximum peaks value"""
        if self._settings_dialog is not None:
            return self._settings_dialog.max_peaks_spin.value()
        else:
            settings = self.get_current_settings()
            return settings['peaks']['max_peaks']
    
    def get_min_peaks(self):
        """Get current minimum peaks value"""
        if self._settings_dialog is not None:
            return self._settings_dialog.min_peaks_spin.value()
        else:
            settings = self.get_current_settings()
            return settings['peaks']['min_peaks']
    
    def set_max_peaks(self, value):
        """Set maximum peaks value"""
        if self._settings_dialog is not None:
            self._settings_dialog.max_peaks_spin.setValue(value)
            # Don't automatically set min_peaks - let user control that separately
        else:
            if self._current_settings is None:
                self._current_settings = self._get_default_settings()
            self._current_settings['peaks']['max_peaks'] = value
            # Also update min_peaks if it's greater than max_peaks to maintain validity
            if self._current_settings['peaks']['min_peaks'] > value:
                self._current_settings['peaks']['min_peaks'] = value
    
    def set_max_peaks_and_apply(self, value, analyzer=None):
        """Set maximum peaks value and apply to analyzer if available"""
        self.set_max_peaks(value)
        if analyzer is not None:
            settings = self.get_current_settings()
            analyzer.set_peak_settings(**settings['peaks'])
    
    def set_min_peaks(self, value):
        """Set minimum peaks value"""
        if self._settings_dialog is not None:
            self._settings_dialog.min_peaks_spin.setValue(value)
        else:
            if self._current_settings is None:
                self._current_settings = self._get_default_settings()
            self._current_settings['peaks']['min_peaks'] = value
            # Also update max_peaks if it's less than min_peaks to maintain validity
            if self._current_settings['peaks']['max_peaks'] < value:
                self._current_settings['peaks']['max_peaks'] = value
    
    def set_min_peaks_and_apply(self, value, analyzer=None):
        """Set minimum peaks value and apply to analyzer if available"""
        self.set_min_peaks(value)
        if analyzer is not None:
            settings = self.get_current_settings()
            analyzer.set_peak_settings(**settings['peaks'])
    
    def sync_with_toolbar_sliders(self, main_window):
        """Synchronize settings with toolbar slider values"""
        if hasattr(main_window, 'onsets_min_slider'):
            current_min_onsets = main_window.onsets_min_slider.value()
            self.set_min_onsets(current_min_onsets)
        
        if hasattr(main_window, 'onsets_max_slider'):
            current_max_onsets = main_window.onsets_max_slider.value()
            self.set_max_onsets(current_max_onsets)
        
        if hasattr(main_window, 'interesting_points_min_slider'):
            current_min_points = main_window.interesting_points_min_slider.value()
            self.set_min_points(current_min_points)
        
        if hasattr(main_window, 'interesting_points_max_slider'):
            current_max_points = main_window.interesting_points_max_slider.value()
            self.set_max_points(current_max_points)
        
        if hasattr(main_window, 'maxima_min_slider'):
            current_min_peaks = main_window.maxima_min_slider.value()
            self.set_min_peaks(current_min_peaks)
        
        if hasattr(main_window, 'maxima_max_slider'):
            current_max_peaks = main_window.maxima_max_slider.value()
            self.set_max_peaks(current_max_peaks)
    
    def update_toolbar_sliders(self, main_window):
        """Update toolbar slider values from current settings"""
        if hasattr(main_window, 'onsets_min_slider'):
            main_window.onsets_min_slider.setValue(self.get_min_onsets())
        
        if hasattr(main_window, 'onsets_max_slider'):
            main_window.onsets_max_slider.setValue(self.get_max_onsets())
        
        if hasattr(main_window, 'interesting_points_min_slider'):
            main_window.interesting_points_min_slider.setValue(self.get_min_points())
        
        if hasattr(main_window, 'interesting_points_max_slider'):
            main_window.interesting_points_max_slider.setValue(self.get_max_points())
        
        if hasattr(main_window, 'maxima_min_slider'):
            main_window.maxima_min_slider.setValue(self.get_min_peaks())
        
        if hasattr(main_window, 'maxima_max_slider'):
            main_window.maxima_max_slider.setValue(self.get_max_peaks())
    
    def save_settings_to_file(self, filename="firework_settings.json"):
        """Save current settings to a JSON file"""
        import json
        import os
        try:
            settings = self.get_current_settings()
            settings_file = os.path.join(os.path.expanduser("~"), ".firework_studio", filename)
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings to file: {e}")
    
    def load_settings_from_file(self, filename="firework_settings.json"):
        """Load settings from a JSON file"""
        import json
        import os
        try:
            settings_file = os.path.join(os.path.expanduser("~"), ".firework_studio", filename)
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                self._current_settings = loaded_settings
                return True
        except Exception as e:
            print(f"Error loading settings from file: {e}")
        return False