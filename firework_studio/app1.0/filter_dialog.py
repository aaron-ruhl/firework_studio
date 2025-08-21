from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QDoubleSpinBox, QPushButton
)

class FilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Apply Audio Filter")
        self.setMinimumWidth(320)
        layout = QVBoxLayout(self)

        # Filter type
        layout.addWidget(QLabel("Filter Type:"))
        self.type_box = QComboBox()
        self.type_box.addItems(["lowpass", "highpass", "bandpass"])
        layout.addWidget(self.type_box)

        # Order
        layout.addWidget(QLabel("Order:"))
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 12)
        self.order_spin.setValue(4)
        layout.addWidget(self.order_spin)

        # Cutoff(s)
        self.cutoff_layout = QHBoxLayout()
        self.cutoff_label = QLabel("Cutoff Frequency (Hz):")
        self.cutoff_layout.addWidget(self.cutoff_label)
        self.cutoff_spin = QDoubleSpinBox()
        self.cutoff_spin.setRange(20, 20000)
        self.cutoff_spin.setValue(1000)
        self.cutoff_spin.setDecimals(1)
        self.cutoff_layout.addWidget(self.cutoff_spin)
        # For bandpass, add second cutoff
        self.cutoff_spin2 = QDoubleSpinBox()
        self.cutoff_spin2.setRange(20, 20000)
        self.cutoff_spin2.setValue(5000)
        self.cutoff_spin2.setDecimals(1)
        self.cutoff_spin2.setVisible(False)
        self.cutoff_layout.addWidget(self.cutoff_spin2)
        layout.addLayout(self.cutoff_layout)

        def update_cutoff_fields():
            filter_type = self.type_box.currentText()
            if filter_type == "bandpass":
                self.cutoff_label.setText("Cutoff Range (Hz):")
                self.cutoff_spin2.setVisible(True)
            else:
                self.cutoff_label.setText("Cutoff Frequency (Hz):")
                self.cutoff_spin2.setVisible(False)
        self.type_box.currentIndexChanged.connect(lambda _: update_cutoff_fields())

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_values(self):
        filter_type = self.type_box.currentText()
        order = self.order_spin.value()
        if filter_type == "bandpass":
            lowcut = self.cutoff_spin.value()
            highcut = self.cutoff_spin2.value()
            # Ensure both are valid floats and lowcut < highcut
            if lowcut is None or highcut is None or not isinstance(lowcut, float) or not isinstance(highcut, float):
                cutoff = (1000.0, 5000.0)
            else:
                cutoff = (min(lowcut, highcut), max(lowcut, highcut))
        else:
            cutoff = self.cutoff_spin.value()
        return filter_type, order, cutoff