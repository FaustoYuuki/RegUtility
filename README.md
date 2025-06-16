# Registry Utility

A comprehensive Python application with a modern graphical interface that combines registry comparison and backup generation functionalities for Windows `.reg` files.

## 🎯 Features

### Registry Comparison
- **Intelligent Comparison**: Compare values from `.reg` files with the current system registry
- **Difference Detection**: Identify values that match, differ, or are missing from the system
- **Visual Filters**: Filter results by type (all, matches, differences, missing)
- **Side-by-Side Display**: Easy visual comparison with color-coded panels

### Registry Backup Generation
- **Smart Backup Creation**: Generate rollback files based on proposed registry changes
- **Current Value Detection**: Automatically detect existing registry values
- **Missing Key Handling**: Handle keys that don't exist in the system
- **Rollback Safety**: Create safe restoration points before applying changes

### Modern Interface
- **Dark Theme**: Modern dark design with rounded corners and shadows
- **Tabbed Interface**: Organized functionality in separate tabs
- **Roboto Fonts**: Clean, modern typography
- **Visual Feedback**: Color-coded results and status indicators

## 🖼️ Interface

The application features a tabbed interface with two main sections:

### Compare Registry Tab
- **Left Panel**: Values from the selected `.reg` file
- **Right Panel**: Current Windows system values
- **Filter Buttons**: Show all, matches only, differences only, or missing only
- **Operation Log**: Detailed information about the comparison process

### Generate Backup Tab
- **File Selection**: Choose the `.reg` file to analyze
- **Backup Generation**: Create rollback files automatically
- **Progress Tracking**: Real-time status updates
- **Success Confirmation**: Clear feedback on completion

## 📸 Screenshot

![image](https://github.com/user-attachments/assets/09836ca5-181f-4d8c-bbc2-bfafc0d0760a)
![image](https://github.com/user-attachments/assets/111e5550-a39c-410a-802c-fd7991780135)



## 🚀 How to Use

### Registry Comparison
1. **Select File**: Click "1. Select .reg File" in the Compare Registry tab
2. **Run Comparison**: Click "2. Compare Registry Values"
3. **View Results**: Results appear in side-by-side panels
4. **Filter Results**: Use filter buttons to focus on specific types

### Backup Generation
1. **Select File**: Click "1. Select .reg File" in the Generate Backup tab
2. **Generate Backup**: Click "2. Generate Backup"
3. **Choose Location**: Select where to save the backup file
4. **Confirmation**: Receive confirmation of successful backup creation

## 📊 Result Types

- ✅ **Matches**: Identical values between file and system
- 🔄 **Differences**: Values that exist but are different
- ❌ **Missing**: Keys/values that do not exist in the system
- ⚠️ **Errors**: Access or read problems

## 🛠️ Requirements

- Windows (for registry access)
- Python 3.7+
- PyQt6

## 📦 Installation

```bash
pip install PyQt6
```

## 🎨 Visual Characteristics

- **Modern Dark Theme**: Non-transparent dark background with shadow effects
- **Rounded Corners**: Smooth, modern interface elements
- **Color-Coded Panels**: Distinct colors for easy identification
- **Roboto Typography**: Professional, readable fonts
- **Depth Effects**: Subtle shadows for visual hierarchy

## 🔧 Technical Features

- **Robust .reg Parsing**: Handles various registry file formats
- **Safe Registry Access**: Secure interface with Windows Registry API
- **Error Handling**: Comprehensive error detection and reporting
- **Memory Efficient**: Optimized for large registry files
- **Cross-Format Support**: UTF-8 and UTF-16 encoding support

## 📝 Use Cases

### Registry Comparison
- Verify if registry modifications have been applied
- Compare configurations between systems
- Audit registry changes
- Debug configuration issues

### Backup Generation
- Create safety backups before applying registry changes
- Generate rollback files for system restoration
- Prepare for safe registry modifications
- Maintain system recovery options

## 👨‍💻 Developed by

yuuki_0711

## 📄 License

This project is open-source and can be freely used for educational and commercial purposes.

