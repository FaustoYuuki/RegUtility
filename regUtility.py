"""
Registry Utility - Clean Code Version
A tool for comparing and backing up Windows Registry files.
"""

import sys
import os
import winreg
from typing import Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MARGIN = 20
LAYOUT_SPACING = 15

REG_FILE_HEADER = "Windows Registry Editor Version 5.00"
REG_FILE_ENCODINGS = ['utf-16', 'utf-8']

STATUS_MATCH = "✅"
STATUS_DIFFERENT_FILE = "📄"
STATUS_DIFFERENT_SYSTEM = "🖥️"
STATUS_NOT_FOUND = "❌"
STATUS_ERROR = "⚠️"

REGISTRY_ROOT_KEYS = {
    "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
    "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
    "HKEY_USERS": winreg.HKEY_USERS,
    "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
}

class ComparisonStatus(Enum):
    MATCH = "match"
    DIFFERENT = "different"
    MISSING = "missing"
    ERROR = "error"
    NOT_WINDOWS = "not_windows"

class SystemStatus(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    NOT_WINDOWS = "not_windows"

@dataclass
class ComparisonResult:
    path: str
    key_name: str
    file_value: str
    system_value: str
    file_display: str
    system_display: str
    match_status: str
    system_status: str

@dataclass
class RegistryKey:
    root_key: str
    sub_key_path: str
    value_name: str

MODERN_DARK_STYLESHEET = """
QMainWindow {
    background-color: #0A0A0A;
    border: 1px solid #2A2A2A;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
}

QWidget {
    background-color: #0A0A0A;
    color: #F5F5F5;
    font-family: "Roboto", "Segoe UI", "Arial", sans-serif;
    font-size: 11pt;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 #6A9DE8, stop:1 #5A7BC8);
    color: white;
    border: none;
    border-radius: 15px;
    padding: 12px 24px;
    font-family: "Roboto", "Segoe UI", "Arial", sans-serif;
    font-weight: bold;
    font-size: 12pt;
    min-height: 20px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 #7AADF8, stop:1 #6A8BD8);
    transform: translateY(-2px);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 #5A8DD8, stop:1 #4A6BB8);
}

QPushButton:disabled {
    background: #404040;
    color: #808080;
}

QTextEdit {
    background-color: rgba(16, 16, 16, 220);
    border: 2px solid #2A2A2A;
    border-radius: 12px;
    padding: 15px;
    color: #F5F5F5;
    font-family: "Consolas", "Courier New", "Monaco", monospace;
    font-size: 10pt;
    selection-background-color: #6A9DE8;
}

QTextEdit[objectName="reg_file_output"] {
    background-color: rgba(16, 16, 32, 220);
    border: 2px solid #4A4A8A;
}

QTextEdit[objectName="system_output"] {
    background-color: rgba(32, 16, 16, 220);
    border: 2px solid #8A4A4A;
}

QTextEdit[objectName="log_output"] {
    background-color: rgba(16, 16, 16, 220);
    border: 2px solid #2A2A2A;
}

QLabel {
    background-color: transparent;
    color: #F5F5F5;
    font-family: "Roboto", "Segoe UI", "Arial", sans-serif;
    font-size: 11pt;
    border: none;
}

QLabel[objectName="title"] {
    font-size: 20pt;
    font-weight: bold;
    color: #6A9DE8;
    padding: 20px 0;
}

QLabel[objectName="instructions"] {
    font-size: 12pt;
    color: #CCCC;
    padding: 10px 0;
}

QLabel[objectName="selected_file"] {
    font-size: 10pt;
    color: #AAAA;
    font-style: italic;
    padding: 5px 0;
}

QLabel[objectName="log_label"] {
    font-size: 12pt;
    font-weight: bold;
    color: #F5F5F5;
    padding: 10px 0;
}

QStatusBar {
    background-color: #121212;
    color: #AAAA;
    font-family: "Roboto", "Segoe UI", "Arial", sans-serif;
    font-size: 9pt;
    border-top: 1px solid #2A2A2A;
    border-radius: 0 0 15px 15px;
}

QTabWidget::pane {
    border: 1px solid #2A2A2A;
    border-radius: 10px;
    background-color: #0A0A0A;
}

QTabBar::tab {
    background: #1A1A1A;
    color: #F5F5F5;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #2A2A2A;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: #0A0A0A;
    border-bottom: 1px solid #0A0A0A;
}

QTabBar::tab:hover {
    background: #2A2A2A;
}
"""

def read_file_with_encoding_fallback(file_path: str) -> str:
    """Read file content with encoding fallback strategy."""
    for encoding in REG_FILE_ENCODINGS:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise IOError(f"Could not read file with any supported encoding: {file_path}")

def validate_reg_file_format(content: str) -> None:
    """Validate that the file is a proper .reg file."""
    lines = content.splitlines()
    if not lines or REG_FILE_HEADER not in lines[0]:
        raise ValueError("Invalid or unsupported .reg file format.")

def parse_registry_line(line: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse a single registry line into key-value pair."""
    if '=' not in line:
        return None, None
    
    try:
        key, value = line.split('=', 1)
        return key.strip().strip('"'), value.strip()
    except ValueError:
        return None, None

def parse_reg_file(file_path: str) -> Dict[str, Dict[str, str]]:
    """Parse a .reg file and return registry settings."""
    content = read_file_with_encoding_fallback(file_path)
    validate_reg_file_format(content)
    
    registry_settings = {}
    current_path = ""
    
    for line in content.splitlines():
        line = line.strip()

        if not line or line.startswith(";"):
            continue
            
        if is_registry_path_line(line):
            current_path = extract_registry_path(line)
            registry_settings[current_path] = {}
        elif current_path:
            key, value = parse_registry_line(line)
            if key and value:
                registry_settings[current_path][key] = value
    
    return registry_settings

def is_registry_path_line(line: str) -> bool:
    """Check if line represents a registry path."""
    return line.startswith('[') and line.endswith(']')

def extract_registry_path(line: str) -> str:
    """Extract registry path from bracketed line."""
    return line[1:-1]

def is_windows_system() -> bool:
    """Check if running on Windows."""
    return os.name == 'nt'

def parse_registry_key_path(full_key_path: str) -> RegistryKey:
    """Parse full registry key path into components."""
    parts = full_key_path.split('\\')
    root_key = parts[0]
    sub_key_path = '\\'.join(parts[1:-1])
    value_name = parts[-1]
    return RegistryKey(root_key, sub_key_path, value_name)

def get_registry_root_key(root_key_str: str) -> Optional[int]:
    """Get Windows registry root key constant."""
    return REGISTRY_ROOT_KEYS.get(root_key_str)

def format_registry_value_by_type(value, reg_type: int) -> str:
    """Format registry value based on its type."""
    formatters = {
        winreg.REG_SZ: lambda v: f'"{v}"',
        winreg.REG_EXPAND_SZ: lambda v: f'hex(2):{v.encode("utf-16-le").hex(",")},00,00',
        winreg.REG_DWORD: lambda v: f'dword:{v:08x}',
        winreg.REG_QWORD: lambda v: f'hex(b):{v:016x}',
        winreg.REG_BINARY: lambda v: f'hex:{"".join([f"{b:02x}," for b in v]).rstrip(",")}',
        winreg.REG_MULTI_SZ: lambda v: f'hex(7):{",".join(s.encode("utf-16-le").hex(",") for s in v)},00,00',
    }
    
    formatter = formatters.get(reg_type)
    if formatter:
        return formatter(value)
    return f'{value} (Type: {reg_type})'

def query_registry_value(registry_key: RegistryKey, log_callback: Callable[[str], None]) -> Tuple[str, str]:
    """Query a single registry value."""
    if not is_windows_system():
        return "N/A (Not on Windows)", SystemStatus.NOT_WINDOWS.value
    
    root_key = get_registry_root_key(registry_key.root_key)
    if not root_key:
        log_callback(f"Warning: Unknown root key: {registry_key.root_key}")
        return f"Unknown root key: {registry_key.root_key}", SystemStatus.ERROR.value
    
    try:
        with winreg.OpenKey(root_key, registry_key.sub_key_path, 0, winreg.KEY_READ) as key_handle:
            value, reg_type = winreg.QueryValueEx(key_handle, registry_key.value_name)
            formatted_value = format_registry_value_by_type(value, reg_type)
            return formatted_value, SystemStatus.FOUND.value
    except FileNotFoundError:
        return f"{STATUS_NOT_FOUND} KEY/VALUE NOT FOUND", SystemStatus.NOT_FOUND.value
    except Exception as e:
        error_msg = f"Error querying value {registry_key.value_name}: {e}"
        log_callback(error_msg)
        return f"{STATUS_ERROR} ERROR: {e}", SystemStatus.ERROR.value

def get_current_registry_value(full_key_path: str, log_callback: Callable[[str], None]) -> Tuple[str, str]:
    """Get current registry value for a given path."""
    try:
        registry_key = parse_registry_key_path(full_key_path)
        return query_registry_value(registry_key, log_callback)
    except Exception as e:
        log_callback(f"Error processing key path {full_key_path}: {e}")
        return f"{STATUS_ERROR} ERROR: {e}", SystemStatus.ERROR.value

def create_comparison_displays(file_value: str, system_value: str, status: ComparisonStatus) -> Tuple[str, str]:
    """Create display strings for comparison results."""
    display_map = {
        ComparisonStatus.MATCH: (f"{STATUS_MATCH} {file_value}", f"{STATUS_MATCH} {system_value}"),
        ComparisonStatus.DIFFERENT: (f"{STATUS_DIFFERENT_FILE} {file_value}", f"{STATUS_DIFFERENT_SYSTEM} {system_value}"),
        ComparisonStatus.MISSING: (file_value, f"{STATUS_NOT_FOUND} KEY/VALUE NOT FOUND"),
        ComparisonStatus.ERROR: (file_value, system_value),
        ComparisonStatus.NOT_WINDOWS: (file_value, system_value),
    }
    return display_map.get(status, (file_value, system_value))

def determine_comparison_status(file_value: str, system_value: str, system_status: str) -> ComparisonStatus:
    """Determine the comparison status between file and system values."""
    if system_status == SystemStatus.NOT_FOUND.value:
        return ComparisonStatus.MISSING
    elif system_status == SystemStatus.ERROR.value:
        return ComparisonStatus.ERROR
    elif system_status == SystemStatus.NOT_WINDOWS.value:
        return ComparisonStatus.NOT_WINDOWS
    elif file_value.strip() == system_value.strip():
        return ComparisonStatus.MATCH
    else:
        return ComparisonStatus.DIFFERENT

def compare_values(file_value: str, system_value: str, system_status: str) -> Tuple[str, str, str]:
    """Compare file value with system value and return formatted results."""
    comparison_status = determine_comparison_status(file_value, system_value, system_status)
    file_display, system_display = create_comparison_displays(file_value, system_value, comparison_status)
    return comparison_status.value, file_display, system_display

def create_backup_entry(value_name: str, value, reg_type: int) -> str:
    """Create a backup registry entry string."""
    formatted_value = format_registry_value_by_type(value, reg_type)
    return f'"{value_name}"={formatted_value}\r\n'

def get_backup_registry_value(registry_key: RegistryKey, log_callback: Callable[[str], None]) -> Optional[str]:
    """Get registry value for backup purposes."""
    if not is_windows_system():
        return None
    
    root_key = get_registry_root_key(registry_key.root_key)
    if not root_key:
        log_callback(f"Warning: Unknown root key: {registry_key.root_key}")
        return None
    
    try:
        with winreg.OpenKey(root_key, registry_key.sub_key_path, 0, winreg.KEY_READ) as key_handle:
            value, reg_type = winreg.QueryValueEx(key_handle, registry_key.value_name)
            return create_backup_entry(registry_key.value_name, value, reg_type)
    except FileNotFoundError:
        return None
    except Exception as e:
        log_callback(f"Error querying value {registry_key.value_name}: {e}")
        return None

def get_current_registry_values_for_backup(parsed_settings: Dict[str, Dict[str, str]], 
                                         log_callback: Callable[[str], None]) -> Dict[str, str]:
    """Get current registry values for backup creation."""
    current_values = {}
    
    if not is_windows_system():
        log_callback("Warning: Not running on Windows. Backup will only contain deletion entries.")
        return {}
    
    for path, keys in parsed_settings.items():
        for key_name in keys.keys():
            full_key_path = f'{path}\\{key_name}'
            try:
                registry_key = parse_registry_key_path(full_key_path)
                backup_entry = get_backup_registry_value(registry_key, log_callback)
                if backup_entry:
                    current_values[full_key_path] = backup_entry
            except Exception as e:
                log_callback(f"Error processing key path {full_key_path}: {e}")
    
    return current_values

def write_backup_file(parsed_settings: Dict[str, Dict[str, str]], 
                     current_values: Dict[str, str], 
                     output_file_path: str) -> None:
    """Write backup registry file."""
    with open(output_file_path, 'w', encoding='utf-16') as file:
        file.write(f'{REG_FILE_HEADER}\r\n\r\n')
        
        for path, keys in parsed_settings.items():
            file.write(f'[{path}]\r\n')
            for key_name in keys.keys():
                full_key_path = f'{path}\\{key_name}'
                if full_key_path in current_values:
                    file.write(current_values[full_key_path])
                else:
                    file.write(f'"{key_name}"=-\r\n')
            file.write('\r\n')

def generate_backup_reg(parsed_settings: Dict[str, Dict[str, str]], 
                       current_values: Dict[str, str], 
                       output_file_path: str) -> None:
    """Generate backup registry file."""
    write_backup_file(parsed_settings, current_values, output_file_path)

def create_title_label(text: str) -> QLabel:
    """Create a styled title label."""
    label = QLabel(text)
    label.setObjectName("title")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label

def create_instructions_label(text: str) -> QLabel:
    """Create a styled instructions label."""
    label = QLabel(text)
    label.setObjectName("instructions")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label

def create_file_selection_label() -> QLabel:
    """Create a file selection status label."""
    label = QLabel("No file selected.")
    label.setObjectName("selected_file")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label

def create_log_label(text: str) -> QLabel:
    """Create a styled log label."""
    label = QLabel(text)
    label.setObjectName("log_label")
    return label

def create_readonly_text_edit(object_name: str) -> QTextEdit:
    """Create a read-only text edit widget."""
    text_edit = QTextEdit()
    text_edit.setObjectName(object_name)
    text_edit.setReadOnly(True)
    return text_edit

class RegistryUtilityApp(QMainWindow):
    """Main application window for Registry Utility."""
    
    def __init__(self):
        super().__init__()
        self.input_file_path_compare = None
        self.input_file_path_backup = None
        self.comparison_results = []
        self._setup_window()
        self._setup_ui()
    
    def _setup_window(self) -> None:
        """Configure main window properties."""
        self.setWindowTitle("Registry Utility - Clean Code Version")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(LAYOUT_SPACING)
        main_layout.setContentsMargins(WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 0; } QTabBar::tab { font-size: 12pt; font-weight: bold; padding: 10px; }")
        main_layout.addWidget(self.tabs)
        
        self._setup_compare_tab()
        self._setup_backup_tab()
        
        self.statusBar().showMessage("Credits: yuuki_0711")
    
    def _setup_compare_tab(self) -> None:
        """Setup the registry comparison tab."""
        compare_widget = QWidget()
        compare_layout = QVBoxLayout(compare_widget)
        compare_layout.setSpacing(LAYOUT_SPACING)
        compare_layout.setContentsMargins(WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN)
        
        compare_layout.addWidget(create_title_label("Registry File vs. System Comparison"))
        compare_layout.addWidget(create_instructions_label(
            "1. Select a .reg file.\n2. Click 'Compare' to see values from the file and your system."
        ))
        
        file_selection_layout = self._create_file_selection_layout_compare()
        compare_layout.addLayout(file_selection_layout)
        
        self.btn_compare = QPushButton("2. Compare Registry Values")
        self.btn_compare.setEnabled(False)
        self.btn_compare.clicked.connect(self._compare_registry)
        compare_layout.addWidget(self.btn_compare)
        
        filter_layout = self._create_filter_buttons_layout()
        compare_layout.addLayout(filter_layout)
        
        comparison_layout = self._create_comparison_output_layout()
        compare_layout.addLayout(comparison_layout)
        
        compare_layout.addWidget(create_log_label("Operation Log:"))
        self.log_output_compare = create_readonly_text_edit("log_output")
        compare_layout.addWidget(self.log_output_compare)
        
        self._log_compare("Ready to start. Please select a .reg file.")
        self.tabs.addTab(compare_widget, "Compare Registry")
    
    def _create_file_selection_layout_compare(self) -> QHBoxLayout:
        """Create file selection layout for compare tab."""
        layout = QHBoxLayout()
        
        self.btn_select_file_compare = QPushButton("1. Select .reg File")
        self.btn_select_file_compare.clicked.connect(self._select_file_compare)
        layout.addWidget(self.btn_select_file_compare)
        
        self.selected_file_label_compare = create_file_selection_label()
        layout.addWidget(self.selected_file_label_compare)
        
        return layout
    
    def _create_filter_buttons_layout(self) -> QHBoxLayout:
        """Create filter buttons layout."""
        layout = QHBoxLayout()
        
        filter_buttons = [
            ("Show All", "all"),
            ("Show Matches Only", "matches"),
            ("Show Differences Only", "differences"),
            ("Show Missing Only", "missing")
        ]
        
        self.filter_buttons = []
        for text, filter_type in filter_buttons:
            button = QPushButton(text)
            button.clicked.connect(lambda checked, ft=filter_type: self._filter_results(ft))
            button.setEnabled(False)
            layout.addWidget(button)
            self.filter_buttons.append(button)
        
        return layout
    
    def _create_comparison_output_layout(self) -> QHBoxLayout:
        """Create comparison output layout."""
        layout = QHBoxLayout()
        
        reg_file_group = QVBoxLayout()
        reg_file_group.addWidget(create_log_label("Values from .reg File:"))
        self.reg_file_output = create_readonly_text_edit("reg_file_output")
        reg_file_group.addWidget(self.reg_file_output)
        layout.addLayout(reg_file_group)
        
        system_group = QVBoxLayout()
        system_group.addWidget(create_log_label("Current System Values:"))
        self.system_output = create_readonly_text_edit("system_output")
        system_group.addWidget(self.system_output)
        layout.addLayout(system_group)
        
        return layout
    
    def _setup_backup_tab(self) -> None:
        """Setup the backup generation tab."""
        backup_widget = QWidget()
        backup_layout = QVBoxLayout(backup_widget)
        backup_layout.setSpacing(LAYOUT_SPACING)
        backup_layout.setContentsMargins(WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN)
        
        backup_layout.addWidget(create_title_label("Registry (.reg) File Backup Generator"))
        backup_layout.addWidget(create_instructions_label(
            "1. Select the .reg file you intend to apply.\n2. Click 'Generate Backup' to create a rollback file."
        ))
        
        self.btn_select_file_backup = QPushButton("1. Select .reg File")
        self.btn_select_file_backup.clicked.connect(self._select_file_backup)
        backup_layout.addWidget(self.btn_select_file_backup)
        
        self.selected_file_label_backup = create_file_selection_label()
        backup_layout.addWidget(self.selected_file_label_backup)
        
        self.btn_generate_backup = QPushButton("2. Generate Backup")
        self.btn_generate_backup.setEnabled(False)
        self.btn_generate_backup.clicked.connect(self._generate_backup)
        backup_layout.addWidget(self.btn_generate_backup)
        
        backup_layout.addWidget(create_log_label("Operation Log:"))
        self.log_output_backup = create_readonly_text_edit("log_output")
        backup_layout.addWidget(self.log_output_backup)
        
        self._log_backup("Ready to start. Please select a .reg file.")
        self.tabs.addTab(backup_widget, "Generate Backup")
    
    def _log_compare(self, message: str) -> None:
        """Log message to compare tab."""
        self.log_output_compare.append(message)
        QApplication.processEvents()
    
    def _log_backup(self, message: str) -> None:
        """Log message to backup tab."""
        self.log_output_backup.append(message)
        QApplication.processEvents()
    
    def _select_file_compare(self) -> None:
        """Handle file selection for compare tab."""
        file_path = self._get_reg_file_path("Select the .reg file to compare")
        if file_path:
            self.input_file_path_compare = file_path
            self.selected_file_label_compare.setText(f"Selected: {os.path.basename(file_path)}")
            self.btn_compare.setEnabled(True)
            self._log_compare(f"Input file selected: {file_path}")
        else:
            self.selected_file_label_compare.setText("File selection cancelled.")
            self.btn_compare.setEnabled(False)
    
    def _select_file_backup(self) -> None:
        """Handle file selection for backup tab."""
        file_path = self._get_reg_file_path("Select the .reg file to back up")
        if file_path:
            self.input_file_path_backup = file_path
            self.selected_file_label_backup.setText(f"Selected: {os.path.basename(file_path)}")
            self.btn_generate_backup.setEnabled(True)
            self._log_backup(f"Input file selected: {file_path}")
        else:
            self.selected_file_label_backup.setText("File selection cancelled.")
            self.btn_generate_backup.setEnabled(False)
    
    def _get_reg_file_path(self, dialog_title: str) -> Optional[str]:
        """Get registry file path from user."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, dialog_title, "", "Registry Files (*.reg);;All Files (*.*)"
        )
        return file_path if file_path else None
    
    def _filter_results(self, filter_type: str) -> None:
        """Filter comparison results based on type."""
        if not self.comparison_results:
            return
        
        self.reg_file_output.clear()
        self.system_output.clear()
        
        current_path = None
        for result in self.comparison_results:
            if self._should_show_result(result, filter_type):
                if current_path != result.path:
                    if current_path is not None:
                        self.reg_file_output.append("")
                        self.system_output.append("")
                    self.reg_file_output.append(f"[{result.path}]")
                    self.system_output.append(f"[{result.path}]")
                    current_path = result.path
                
                self.reg_file_output.append(f'  "{result.key_name}"={result.file_display}')
                self.system_output.append(f'  "{result.key_name}"={result.system_display}')
    
    def _should_show_result(self, result: ComparisonResult, filter_type: str) -> bool:
        """Determine if result should be shown based on filter."""
        filter_map = {
            "all": True,
            "matches": result.match_status == ComparisonStatus.MATCH.value,
            "differences": result.match_status == ComparisonStatus.DIFFERENT.value,
            "missing": result.match_status == ComparisonStatus.MISSING.value,
        }
        return filter_map.get(filter_type, False)
    
    def _compare_registry(self) -> None:
        """Perform registry comparison."""
        if not self.input_file_path_compare:
            self._log_compare("Error: No input file has been selected.")
            return
        
        self._log_compare("\nStarting registry comparison...")
        self._clear_comparison_outputs()
        
        try:
            parsed_settings = self._parse_input_file(self.input_file_path_compare, self._log_compare)
            comparison_stats = self._perform_comparison(parsed_settings)
            self._enable_filter_buttons()
            self._show_comparison_summary(comparison_stats)
            self._show_completion_dialog(comparison_stats)
        except Exception as e:
            self._handle_error(str(e), self._log_compare)
    
    def _clear_comparison_outputs(self) -> None:
        """Clear comparison output areas."""
        self.reg_file_output.clear()
        self.system_output.clear()
        self.comparison_results = []
    
    def _parse_input_file(self, file_path: str, log_callback: Callable[[str], None]) -> Dict[str, Dict[str, str]]:
        """Parse input registry file."""
        log_callback("Step 1: Parsing .reg file...")
        parsed_settings = parse_reg_file(file_path)
        log_callback(f"Parsing complete. Found {len(parsed_settings)} key sections.")
        return parsed_settings
    
    def _perform_comparison(self, parsed_settings: Dict[str, Dict[str, str]]) -> Dict[str, int]:
        """Perform the actual comparison and return statistics."""
        self._log_compare("Step 2: Comparing values...")
        
        stats = {"total": 0, "matches": 0, "differences": 0, "missing": 0, "errors": 0}
        
        for path, keys in parsed_settings.items():
            self._add_path_headers(path)
            
            for key_name, file_value in keys.items():
                result = self._compare_single_value(path, key_name, file_value)
                self.comparison_results.append(result)
                self._update_stats(stats, result.match_status)
                self._add_comparison_output(result)
            
            self._add_section_separator()
        
        return stats
    
    def _add_path_headers(self, path: str) -> None:
        """Add path headers to output."""
        self.reg_file_output.append(f"[{path}]")
        self.system_output.append(f"[{path}]")
    
    def _compare_single_value(self, path: str, key_name: str, file_value: str) -> ComparisonResult:
        """Compare a single registry value."""
        full_key_path = f'{path}\\{key_name}'
        system_value, system_status = get_current_registry_value(full_key_path, self._log_compare)
        match_status, file_display, system_display = compare_values(file_value, system_value, system_status)
        
        return ComparisonResult(
            path=path,
            key_name=key_name,
            file_value=file_value,
            system_value=system_value,
            file_display=file_display,
            system_display=system_display,
            match_status=match_status,
            system_status=system_status
        )
    
    def _update_stats(self, stats: Dict[str, int], match_status: str) -> None:
        """Update comparison statistics."""
        stats["total"] += 1
        if match_status == ComparisonStatus.MATCH.value:
            stats["matches"] += 1
        elif match_status == ComparisonStatus.DIFFERENT.value:
            stats["differences"] += 1
        elif match_status == ComparisonStatus.MISSING.value:
            stats["missing"] += 1
        elif match_status == ComparisonStatus.ERROR.value:
            stats["errors"] += 1
    
    def _add_comparison_output(self, result: ComparisonResult) -> None:
        """Add comparison result to output."""
        self.reg_file_output.append(f'  "{result.key_name}"={result.file_display}')
        self.system_output.append(f'  "{result.key_name}"={result.system_display}')
    
    def _add_section_separator(self) -> None:
        """Add section separator to output."""
        self.reg_file_output.append("")
        self.system_output.append("")
    
    def _enable_filter_buttons(self) -> None:
        """Enable filter buttons after comparison."""
        for button in self.filter_buttons:
            button.setEnabled(True)
    
    def _show_comparison_summary(self, stats: Dict[str, int]) -> None:
        """Show comparison summary in log."""
        self._log_compare(f"\n📊 COMPARISON SUMMARY:")
        self._log_compare(f"  Total keys compared: {stats['total']}")
        self._log_compare(f"  {STATUS_MATCH} Matches: {stats['matches']}")
        self._log_compare(f"  🔄 Differences: {stats['differences']}")
        self._log_compare(f"  {STATUS_NOT_FOUND} Missing from system: {stats['missing']}")
        self._log_compare(f"  {STATUS_ERROR} Errors: {stats['errors']}")
        self._log_compare("Comparison complete.")
    
    def _show_completion_dialog(self, stats: Dict[str, int]) -> None:
        """Show completion dialog with statistics."""
        message = (
            f"Registry comparison finished!\n\n"
            f"Total: {stats['total']} keys\n"
            f"Matches: {stats['matches']}\n"
            f"Differences: {stats['differences']}\n"
            f"Missing: {stats['missing']}\n"
            f"Errors: {stats['errors']}"
        )
        QMessageBox.information(self, "Comparison Complete", message)
    
    def _generate_backup(self) -> None:
        """Generate backup registry file."""
        if not self.input_file_path_backup:
            self._log_backup("Error: No input file has been selected.")
            return
        
        self._log_backup("\nStarting backup process...")
        self._set_backup_ui_busy(True)
        
        try:
            parsed_settings = self._parse_input_file(self.input_file_path_backup, self._log_backup)
            current_values = self._get_current_values_for_backup(parsed_settings)
            output_path = self._get_backup_output_path()
            
            if output_path:
                self._create_backup_file(parsed_settings, current_values, output_path)
                self._show_backup_success(output_path)
        except Exception as e:
            self._handle_error(str(e), self._log_backup)
        finally:
            self._set_backup_ui_busy(False)
    
    def _get_current_values_for_backup(self, parsed_settings: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        """Get current registry values for backup."""
        self._log_backup("Step 2: Reading current values from the Windows Registry...")
        current_values = get_current_registry_values_for_backup(parsed_settings, self._log_backup)
        self._log_backup("Reading current values complete.")
        return current_values
    
    def _get_backup_output_path(self) -> Optional[str]:
        """Get output path for backup file."""
        default_name = f"{os.path.splitext(os.path.basename(self.input_file_path_backup))[0]}_backup.reg"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save backup .reg file as", default_name, "Registry Files (*.reg);;All Files (*.*)"
        )
        
        if not output_path:
            self._log_backup("Operation cancelled: No save location was selected.")
        
        return output_path
    
    def _create_backup_file(self, parsed_settings: Dict[str, Dict[str, str]], 
                           current_values: Dict[str, str], output_path: str) -> None:
        """Create the backup file."""
        self._log_backup("Step 3: Generating the backup file...")
        generate_backup_reg(parsed_settings, current_values, output_path)
    
    def _show_backup_success(self, output_path: str) -> None:
        """Show backup success message."""
        success_msg = f"Backup file successfully generated at: {output_path}"
        self._log_backup("\n----")
        self._log_backup(f"{STATUS_MATCH} SUCCESS!")
        self._log_backup(success_msg)
        self._log_backup("----")
        QMessageBox.information(self, "Success", success_msg)
    
    def _set_backup_ui_busy(self, busy: bool) -> None:
        """Set backup UI busy state."""
        self.btn_select_file_backup.setEnabled(not busy)
        self.btn_generate_backup.setEnabled(not busy and self.input_file_path_backup is not None)
    
    def _handle_error(self, error_message: str, log_callback: Callable[[str], None]) -> None:
        """Handle and display errors."""
        formatted_error = f"{STATUS_ERROR} ERROR: {error_message}"
        log_callback("\n----")
        log_callback(formatted_error)
        log_callback("----")
        QMessageBox.critical(self, "Operation Error", error_message)

def validate_windows_system() -> None:
    """Validate that the application is running on Windows."""
    if not is_windows_system():
        app = QApplication(sys.argv)
        app.setStyleSheet(MODERN_DARK_STYLESHEET)
        QMessageBox.critical(
            None,
            "Compatibility Error",
            "This program requires the Windows Registry and can only be run on a Windows OS."
        )
        sys.exit(1)

def main() -> None:
    """Main application entry point."""
    validate_windows_system()
    
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_DARK_STYLESHEET)
    
    window = RegistryUtilityApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
