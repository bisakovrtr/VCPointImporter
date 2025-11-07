# Point Importer Package for Visual Components

This package provides CSV point import and export tools for Visual Components 4.10, enabling easy transfer of 3D points and joint angles between CSV files and robot routines.

## Overview

The Point Importer package consists of three main modules:

1. **CSV Point Import** (`importPointsCSV.py`) - Import 3D points or joint angles from CSV files into robot routines
2. **CSV Point Export** (`exportPointsCSV.py`) - Export 3D points or joint angles from robot routines to CSV files
3. **Test Script** (`testScript.py`) - Utility script for testing robot program statements

## Installation

1. Copy the entire `PointImporter` folder to your Visual Components commands directory
2. Restart Visual Components
3. The tools will appear in the `VcTabTeach/Beck` menu and the main `Tools` menu

## Usage Workflow

### 1. CSV Point Import

**Purpose**: Import 3D points or joint angles from CSV files into robot routines.

**CSV Format**:
- **Position only**: `X,Y,Z`
- **Full pose**: `X,Y,Z,W,P,R` (W,P,R in degrees)
- **Joint angles**: `J1,J2,J3,...,J6` (variable number of joints, in degrees)
- **Separators**: Comma (`,`) or semicolon (`;`)
- **Empty lines**: Automatically ignored
- **Invalid lines**: Skipped with warning messages

**Steps**:
1. Select an active robot routine
2. Run "Import Points" from the `VcTabTeach/Beck` menu or `Tools` menu
3. Select your CSV file
4. Choose import format (Coordinates or Joint Angles)
5. Points are imported as PTP motion statements

**Example CSV (Coordinates)**:
```csv
1167,154,499.2820845,0,0,0
868.9,169.4,499.9104026,0,0,0
854.32,-130.35,499.8580429,0,0,0
491.9,-133.3,487.9,-180,0,-90
```

**Example CSV (Joint Angles)**:
```csv
45.0,30.0,-90.0,0.0,60.0,0.0
90.0,45.0,-120.0,15.0,75.0,30.0
```

### 2. CSV Point Export

**Purpose**: Export 3D points or joint angles from robot routines to CSV files for backup or analysis.

**Export Formats**:
- **Position only**: `X,Y,Z` coordinates
- **Full pose**: `X,Y,Z,W,P,R` coordinates (W,P,R in degrees)
- **Joint angles**: `J1,J2,J3,...,J6` (variable number of joints, in degrees)
- **Precision**: 6 decimal places for all coordinates
- **Separators**: Comma (`,`)

**Steps**:
1. Select an active robot routine containing motion statements
2. Run "Export Points" from the `VcTabTeach/Beck` menu or `Tools` menu
3. Choose save location and file name
4. Select export format (Position Only, Full Pose, or Joint Angles)
5. Points are exported from PTP, LIN, PATH, and CUSTOM motion statements

**Features**:
- Extracts points from all valid motion statement types
- Handles coordinate system transformations automatically
- Provides detailed error reporting for failed extractions
- Supports position-only, full pose, and joint angle data export
- Handles path statements with multiple positions

### 3. Test Script

**Purpose**: Utility script for testing and debugging robot program statements.

**Steps**:
1. Select an active robot
2. Run "Test Script" from the `VcTabTeach/Beck` menu or `Tools` menu
3. The script prints information about all statements in the robot's main routine

## Features

### Performance Enhancements

1. **File Handling**: 
   - Proper file closure with context managers
   - Better error handling for file operations
   - Support for both comma and semicolon separators

2. **Error Handling**:
   - Comprehensive validation of input data
   - Detailed error messages with line numbers
   - Graceful handling of invalid data

### Code Quality Improvements

1. **Documentation**:
   - Comprehensive docstrings for all functions
   - Inline comments explaining complex algorithms
   - Clear parameter and return value descriptions

2. **Structure**:
   - Separation of concerns into focused functions
   - Consistent naming conventions
   - Proper global variable management

3. **Validation**:
   - Input parameter validation
   - User-friendly error messages

## Error Handling

The code includes comprehensive error handling:

- **File Operations**: IOError handling for file access issues
- **Data Validation**: Checking for valid CSV format and numeric data
- **User Input**: Validation of robot and routine selection
- **Mathematical Operations**: Handling of invalid numeric data
- **Joint Angle Import**: Multiple fallback methods for setting joint values

## Troubleshooting

### Common Issues

1. **"No robot selected"**: Ensure a robot is active in the teach context
2. **"File not found"**: Verify CSV file path and permissions
3. **"Invalid data"**: Check CSV format and numeric values
4. **Joint angle import fails**: Ensure joint angles are in degrees and match robot's number of joints
5. **Orientation not preserved**: Check that WPR values are included in CSV for full pose import

### Best Practices

1. **CSV Format**: Use consistent separators (comma or semicolon) throughout the file
2. **Data Precision**: Export uses 6 decimal places; import accepts any valid numeric format
3. **Joint Angles**: Verify joint angle units (degrees) match your robot controller requirements
4. **Coordinate Systems**: Points are imported/exported in the robot's reference coordinate system

## Technical Details

### Dependencies
- Visual Components 4.10 API
- vcCommand, vcMatrix modules
- Standard Python math library

### Coordinate Systems
- All points are imported/exported in the robot's reference coordinate system
- Automatic transformation handled by Visual Components API
- Support for robot base coordinate systems

### Joint Angle Handling
- Joint angles are stored and imported in degrees
- Forward kinematics conversion to radians handled automatically when needed
- Supports variable number of joints (typically 6 for industrial robots)

## Version History



## Support


