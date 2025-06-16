import sys
import os
import winreg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox, QTabWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# =============================================================================
# MODERN DARK STYLESHEET WITH ROUNDED CORNERS AND SHADOWS
# =============================================================================
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
    color: #CCCCCC;
    padding: 10px 0;
}

QLabel[objectName="selected_file"] {
    font-size: 10pt;
    color: #AAAAAA;
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
    color: #AAAAAA;
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

def parse_reg_file(file_path):
    registry_settings = {}
    current_path = ""
    try:
        with open(file_path, 'r', encoding='utf-16') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"Could not read the file: {e}")
    except Exception as e:
        raise IOError(f"Could not read the file: {e}")

    lines = content.splitlines()
    if not lines or "Windows Registry Editor Version 5.00" not in lines[0]:
        raise ValueError("Invalid or unsupported .reg file format.")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('[') and line.endswith(']'):
            current_path = line[1:-1]
            registry_settings[current_path] = {}
        elif current_path and '=' in line:
            try:
                key, value = line.split('=', 1)
                key = key.strip().strip('"')
                registry_settings[current_path][key] = value.strip()
            except ValueError:
                pass 
    return registry_settings

def get_current_registry_value(full_key_path, log_callback):
    if os.name != 'nt':
        return "N/A (Not on Windows)", "not_windows"

    try:
        parts = full_key_path.split('\\')
        root_key_str = parts[0]
        sub_key_path = '\\'.join(parts[1:-1])
        key_name = parts[-1]

        root_key_map = {
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
        }

        root_key = root_key_map.get(root_key_str)
        if not root_key:
            log_callback(f"Warning: Unknown root key: {root_key_str}")
            return f"Unknown root key: {root_key_str}", "error"

        try:
            with winreg.OpenKey(root_key, sub_key_path, 0, winreg.KEY_READ) as key_handle:
                value, reg_type = winreg.QueryValueEx(key_handle, key_name)
                
                if reg_type == winreg.REG_SZ:
                    return f'"{value}"', "found"
                elif reg_type == winreg.REG_EXPAND_SZ:
                    hex_value = value.encode('utf-16-le').hex(',') + ',00,00'
                    return f'hex(2):{hex_value}', "found"
                elif reg_type == winreg.REG_DWORD:
                    return f'dword:{value:08x}', "found"
                elif reg_type == winreg.REG_QWORD:
                    return f'hex(b):{value:016x}', "found"
                elif reg_type == winreg.REG_BINARY:
                    hex_value = ''.join([f'{b:02x},' for b in value]).rstrip(',')
                    return f'hex:{hex_value}', "found"
                elif reg_type == winreg.REG_MULTI_SZ:
                    hex_data = ','.join(s.encode('utf-16-le').hex(',') for s in value) + ',00,00'
                    return f'hex(7):{hex_data}', "found"
                else:
                    return f'{value} (Type: {reg_type})', "found"
        except FileNotFoundError:
            return "❌ KEY/VALUE NOT FOUND", "not_found"
        except Exception as e:
            log_callback(f"Error querying value {key_name} in {full_key_path}: {e}")
            return f"❌ ERROR: {e}", "error"
    except Exception as e:
        log_callback(f"Error processing key path {full_key_path}: {e}")
        return f"❌ ERROR: {e}", "error"

def compare_values(file_value, system_value, system_status):
    if system_status == "not_found":
        return "missing", file_value, "❌ KEY/VALUE NOT FOUND"
    elif system_status == "error":
        return "error", file_value, system_value
    elif system_status == "not_windows":
        return "not_windows", file_value, system_value
    else:
        if file_value.strip() == system_value.strip():
            return "match", f"✅ {file_value}", f"✅ {system_value}"
        else:
            return "different", f"📄 {file_value}", f"🖥️ {system_value}"

def get_current_registry_values_for_backup(parsed_settings, log_callback):
    current_values = {}
    if os.name != 'nt':
        log_callback("Warning: This script is not running on Windows. The backup will only contain deletion entries.")
        return {}

    for path, keys in parsed_settings.items():
        try:
            root_key_str, sub_key_path = path.split('\\', 1)
        except ValueError:
            log_callback(f"Warning: Skipped invalid key path: {path}")
            continue

        root_key_map = {
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
        }

        root_key = root_key_map.get(root_key_str)
        if not root_key:
            log_callback(f"Warning: Skipped unknown root key: {root_key_str}")
            continue

        try:
            with winreg.OpenKey(root_key, sub_key_path, 0, winreg.KEY_READ) as key_handle:
                for key_name in keys.keys():
                    full_key_path = f'{path}\\{key_name}'
                    try:
                        value, reg_type = winreg.QueryValueEx(key_handle, key_name)
                        
                        if reg_type == winreg.REG_SZ:
                            current_values[full_key_path] = f'"{key_name}"="{value}"\r\n'
                        elif reg_type == winreg.REG_EXPAND_SZ:
                            hex_value = value.encode('utf-16-le').hex(',') + ',00,00'
                            current_values[full_key_path] = f'"{key_name}"=hex(2):{hex_value}\r\n'
                        elif reg_type == winreg.REG_DWORD:
                            current_values[full_key_path] = f'"{key_name}"=dword:{value:08x}\r\n'
                        elif reg_type == winreg.REG_QWORD:
                            current_values[full_key_path] = f'"{key_name}"=hex(b):{value:016x}\r\n'
                        elif reg_type == winreg.REG_BINARY:
                            hex_value = ''.join([f'{b:02x},' for b in value]).rstrip(',')
                            current_values[full_key_path] = f'"{key_name}"=hex:{hex_value}\r\n'
                        elif reg_type == winreg.REG_MULTI_SZ:
                            hex_data = ','.join(s.encode('utf-16-le').hex(',') for s in value) + ',00,00'
                            current_values[full_key_path] = f'"{key_name}"=hex(7):{hex_data}\r\n'
                        
                    except FileNotFoundError:
                        pass
                    except Exception as e:
                        log_callback(f"Error querying value {key_name} in {path}: {e}")
        except FileNotFoundError:
            pass
        except Exception as e:
            log_callback(f"Error opening key {path}: {e}")

    return current_values

def generate_backup_reg(parsed_settings, current_values, output_file_path):
    with open(output_file_path, 'w', encoding='utf-16') as f:
        f.write('Windows Registry Editor Version 5.00\r\n\r\n')

        for path, keys in parsed_settings.items():
            f.write(f'[{path}]\r\n')
            for key_name in keys.keys():
                full_key_path = f'{path}\\{key_name}'
                if full_key_path in current_values:
                    f.write(current_values[full_key_path])
                else:
                    f.write(f'"{key_name}"=-\r\n')
            f.write('\r\n')

class UnifiedRegApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.input_file_path = None
        self.setWindowTitle("Unified Registry Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 0; } QTabBar::tab { font-size: 12pt; font-weight: bold; padding: 10px; }")
        main_layout.addWidget(self.tabs)

        self.setup_compare_tab()
        self.setup_backup_tab()

        self.statusBar().showMessage("Credits: yuuki_0711")

    def log(self, message):
        # This log will be shared by both tabs
        # For now, let's just print to console or a dedicated log area if we add one later
        print(message)

    def setup_compare_tab(self):
        compare_widget = QWidget()
        compare_layout = QVBoxLayout(compare_widget)
        compare_layout.setSpacing(15)
        compare_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("Registry File vs. System Comparison")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compare_layout.addWidget(title_label)
        
        instructions_label = QLabel(
            "1. Select a .reg file.\n"
            "2. Click 'Compare' to see values from the file and your system."
        )
        instructions_label.setObjectName("instructions")
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compare_layout.addWidget(instructions_label)

        file_selection_layout = QHBoxLayout()
        self.btn_select_file_compare = QPushButton("1. Select .reg File")
        self.btn_select_file_compare.clicked.connect(self.select_file_compare)
        file_selection_layout.addWidget(self.btn_select_file_compare)

        self.selected_file_label_compare = QLabel("No file selected.")
        self.selected_file_label_compare.setObjectName("selected_file")
        self.selected_file_label_compare.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_selection_layout.addWidget(self.selected_file_label_compare)
        compare_layout.addLayout(file_selection_layout)
        
        self.btn_compare = QPushButton("2. Compare Registry Values")
        self.btn_compare.setEnabled(False)
        self.btn_compare.clicked.connect(self.compare_registry)
        compare_layout.addWidget(self.btn_compare)

        filter_layout = QHBoxLayout()
        self.btn_show_all = QPushButton("Show All")
        self.btn_show_matches = QPushButton("Show Matches Only")
        self.btn_show_differences = QPushButton("Show Differences Only")
        self.btn_show_missing = QPushButton("Show Missing Only")
        
        self.btn_show_all.clicked.connect(lambda: self.filter_results("all"))
        self.btn_show_matches.clicked.connect(lambda: self.filter_results("matches"))
        self.btn_show_differences.clicked.connect(lambda: self.filter_results("differences"))
        self.btn_show_missing.clicked.connect(lambda: self.filter_results("missing"))
        
        filter_layout.addWidget(self.btn_show_all)
        filter_layout.addWidget(self.btn_show_matches)
        filter_layout.addWidget(self.btn_show_differences)
        filter_layout.addWidget(self.btn_show_missing)
        
        for btn in [self.btn_show_all, self.btn_show_matches, self.btn_show_differences, self.btn_show_missing]:
            btn.setEnabled(False)
        
        compare_layout.addLayout(filter_layout)

        comparison_layout = QHBoxLayout()

        reg_file_group = QVBoxLayout()
        reg_file_label = QLabel("Values from .reg File:")
        reg_file_label.setObjectName("log_label")
        reg_file_group.addWidget(reg_file_label)
        self.reg_file_output = QTextEdit()
        self.reg_file_output.setObjectName("reg_file_output")
        self.reg_file_output.setReadOnly(True)
        reg_file_group.addWidget(self.reg_file_output)
        comparison_layout.addLayout(reg_file_group)

        system_group = QVBoxLayout()
        system_label = QLabel("Current System Values:")
        system_label.setObjectName("log_label")
        system_group.addWidget(system_label)
        self.system_output = QTextEdit()
        self.system_output.setObjectName("system_output")
        self.system_output.setReadOnly(True)
        system_group.addWidget(self.system_output)
        comparison_layout.addLayout(system_group)

        compare_layout.addLayout(comparison_layout)

        log_label = QLabel("Operation Log:")
        log_label.setObjectName("log_label")
        compare_layout.addWidget(log_label)
        
        self.log_output_compare = QTextEdit()
        self.log_output_compare.setObjectName("log_output")
        self.log_output_compare.setReadOnly(True)
        compare_layout.addWidget(self.log_output_compare)
        
        self.comparison_results = []
        self.log_compare("Ready to start. Please select a .reg file.")

        self.tabs.addTab(compare_widget, "Compare Registry")

    def log_compare(self, message):
        self.log_output_compare.append(message)
        QApplication.processEvents()

    def select_file_compare(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select the .reg file to compare",
            "",
            "Registry Files (*.reg);;All Files (*.*)"
        )
        if file_path:
            self.input_file_path_compare = file_path
            self.selected_file_label_compare.setText(f"Selected: {os.path.basename(file_path)}")
            self.btn_compare.setEnabled(True)
            self.log_compare(f"Input file selected: {file_path}")
        else:
            self.selected_file_label_compare.setText("File selection cancelled.")
            self.btn_compare.setEnabled(False)

    def filter_results(self, filter_type):
        if not self.comparison_results:
            return
            
        self.reg_file_output.clear()
        self.system_output.clear()
        
        for result in self.comparison_results:
            path = result['path']
            key_name = result['key_name']
            file_display = result['file_display']
            system_display = result['system_display']
            match_status = result['match_status']
            
            should_show = False
            if filter_type == "all":
                should_show = True
            elif filter_type == "matches" and match_status == "match":
                should_show = True
            elif filter_type == "differences" and match_status == "different":
                should_show = True
            elif filter_type == "missing" and match_status == "missing":
                should_show = True
                
            if should_show:
                if not self.reg_file_output.toPlainText().endswith(f"[{path}]\n"):
                    if self.reg_file_output.toPlainText():
                        self.reg_file_output.append("")
                        self.system_output.append("")
                    self.reg_file_output.append(f"[{path}]")
                    self.system_output.append(f"[{path}]")
                
                self.reg_file_output.append(f'  "{key_name}"={file_display}')
                self.system_output.append(f'  "{key_name}"={system_display}')

    def compare_registry(self):
        if not self.input_file_path_compare:
            self.log_compare("Error: No input file has been selected.")
            return

        self.log_compare("\nStarting registry comparison...")
        self.reg_file_output.clear()
        self.system_output.clear()
        self.comparison_results = []

        try:
            self.log_compare("Step 1: Parsing .reg file...")
            parsed_settings = parse_reg_file(self.input_file_path_compare)
            self.log_compare(f"Parsing complete. Found {len(parsed_settings)} key sections.")

            self.log_compare("Step 2: Comparing values...")
            
            total_keys = sum(len(keys) for keys in parsed_settings.values())
            matches = 0
            differences = 0
            missing = 0
            errors = 0
            
            for path, keys in parsed_settings.items():
                self.reg_file_output.append(f"[{path}]")
                self.system_output.append(f"[{path}]")
                
                for key_name, file_value in keys.items():
                    full_key_path = f'{path}\\{key_name}'
                    system_value, system_status = get_current_registry_value(full_key_path, self.log_compare)
                    
                    match_status, file_display, system_display = compare_values(file_value, system_value, system_status)
                    
                    self.comparison_results.append({
                        'path': path,
                        'key_name': key_name,
                        'file_value': file_value,
                        'system_value': system_value,
                        'file_display': file_display,
                        'system_display': system_display,
                        'match_status': match_status,
                        'system_status': system_status
                    })
                    
                    if match_status == "match":
                        matches += 1
                    elif match_status == "different":
                        differences += 1
                    elif match_status == "missing":
                        missing += 1
                    elif match_status == "error":
                        errors += 1

                    self.reg_file_output.append(f'  "{key_name}"={file_display}')
                    self.system_output.append(f'  "{key_name}"={system_display}')
                    
                self.reg_file_output.append("")
                self.system_output.append("")

            for btn in [self.btn_show_all, self.btn_show_matches, self.btn_show_differences, self.btn_show_missing]:
                btn.setEnabled(True)

            self.log_compare(f"\n📊 COMPARISON SUMMARY:")
            self.log_compare(f"  Total keys compared: {total_keys}")
            self.log_compare(f"  ✅ Matches: {matches}")
            self.log_compare(f"  🔄 Differences: {differences}")
            self.log_compare(f"  ❌ Missing from system: {missing}")
            self.log_compare(f"  ⚠️ Errors: {errors}")
            
            self.log_compare("Comparison complete.")
            QMessageBox.information(self, "Comparison Complete", 
                                  f"Registry comparison finished!\n\n"
                                  f"Total: {total_keys} keys\n"
                                  f"Matches: {matches}\n"
                                  f"Differences: {differences}\n"
                                  f"Missing: {missing}\n"
                                  f"Errors: {errors}")

        except Exception as e:
            error_message = f"❌ ERROR: {e}"
            self.log_compare(error_message)
            QMessageBox.critical(self, "Operation Error", str(e))

    def setup_backup_tab(self):
        backup_widget = QWidget()
        backup_layout = QVBoxLayout(backup_widget)
        backup_layout.setSpacing(15)
        backup_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("Registry (.reg) File Backup Generator")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        backup_layout.addWidget(title_label)
        
        instructions_label = QLabel(
            "1. Select the .reg file you intend to apply.\n"
            "2. Click 'Generate Backup' to create a rollback file."
        )
        instructions_label.setObjectName("instructions")
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        backup_layout.addWidget(instructions_label)

        self.btn_select_file_backup = QPushButton("1. Select .reg File")
        self.btn_select_file_backup.clicked.connect(self.select_file_backup)
        backup_layout.addWidget(self.btn_select_file_backup)

        self.selected_file_label_backup = QLabel("No file selected.")
        self.selected_file_label_backup.setObjectName("selected_file")
        self.selected_file_label_backup.setAlignment(Qt.AlignmentFlag.AlignCenter)
        backup_layout.addWidget(self.selected_file_label_backup)
        
        self.btn_generate_backup = QPushButton("2. Generate Backup")
        self.btn_generate_backup.setEnabled(False)
        self.btn_generate_backup.clicked.connect(self.generate_backup)
        backup_layout.addWidget(self.btn_generate_backup)

        log_label = QLabel("Operation Log:")
        log_label.setObjectName("log_label")
        backup_layout.addWidget(log_label)
        
        self.log_output_backup = QTextEdit()
        self.log_output_backup.setObjectName("log_output")
        self.log_output_backup.setReadOnly(True)
        backup_layout.addWidget(self.log_output_backup)
        
        self.log_backup("Ready to start. Please select a .reg file.")

        self.tabs.addTab(backup_widget, "Generate Backup")

    def log_backup(self, message):
        self.log_output_backup.append(message)
        QApplication.processEvents()

    def select_file_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select the .reg file to back up",
            "",
            "Registry Files (*.reg);;All Files (*.*)"
        )
        if file_path:
            self.input_file_path_backup = file_path
            self.selected_file_label_backup.setText(f"Selected: {os.path.basename(file_path)}")
            self.btn_generate_backup.setEnabled(True)
            self.log_backup(f"Input file selected: {file_path}")
        else:
            self.selected_file_label_backup.setText("File selection cancelled.")
            self.btn_generate_backup.setEnabled(False)

    def generate_backup(self):
        if not self.input_file_path_backup:
            self.log_backup("Error: No input file has been selected.")
            return

        self.log_backup("\nStarting backup process...")
        self.set_ui_busy_backup(True)

        try:
            self.log_backup("Step 1: Parsing .reg file...")
            parsed_settings = parse_reg_file(self.input_file_path_backup)
            self.log_backup(f"Parsing complete. Found {len(parsed_settings)} key sections.")

            self.log_backup("Step 2: Reading current values from the Windows Registry...")
            current_values = get_current_registry_values_for_backup(parsed_settings, self.log_backup)
            self.log_backup("Reading current values complete.")

            output_file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save backup .reg file as",
                f"{os.path.splitext(os.path.basename(self.input_file_path_backup))[0]}_backup.reg",
                "Registry Files (*.reg);;All Files (*.*)"
            )

            if not output_file_path:
                self.log_backup("Operation cancelled: No save location was selected.")
                self.set_ui_busy_backup(False)
                return

            self.log_backup("Step 3: Generating the backup file...")
            generate_backup_reg(parsed_settings, current_values, output_file_path)
            
            success_msg = f"Backup file successfully generated at: {output_file_path}"
            self.log_backup("\n----------------------------------------------------")
            self.log_backup("✅ SUCCESS!")
            self.log_backup(success_msg)
            self.log_backup("----------------------------------------------------")
            QMessageBox.information(self, "Success", success_msg)

        except Exception as e:
            error_message = f"❌ ERROR: {e}"
            self.log_backup("\n----------------------------------------------------")
            self.log_backup(error_message)
            self.log_backup("----------------------------------------------------")
            QMessageBox.critical(self, "Operation Error", str(e))
        finally:
            self.set_ui_busy_backup(False)

    def set_ui_busy_backup(self, busy):
        self.btn_select_file_backup.setEnabled(not busy)
        self.btn_generate_backup.setEnabled(not busy and self.input_file_path_backup is not None)

if __name__ == '__main__':
    if os.name != 'nt':
        app = QApplication(sys.argv)
        app.setStyleSheet(MODERN_DARK_STYLESHEET)
        QMessageBox.critical(
            None, 
            "Compatibility Error", 
            "This program requires the Windows Registry and can only be run on a Windows OS."
        )
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_DARK_STYLESHEET)
    
    window = UnifiedRegApp()
    window.show()
    sys.exit(app.exec())


