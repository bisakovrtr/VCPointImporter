# -------------------------------------------------------------------------------
# CSV Point Export Module for Robot Calibration
#
# This module exports 3D points from robot routines to CSV files.
# Supports three data formats:
# - Position only (X,Y,Z): Cartesian coordinates
# - Full pose (X,Y,Z,W,P,R): Cartesian coordinates with orientation
# - Joint angles (J1,J2,J3,...): Robot joint angles (independent of base and TCP)
#
# CSV Format:
# - Position only: X,Y,Z
# - Full pose: X,Y,Z,W,P,R (W,P,R in degrees)
# - Joint angles: J1,J2,J3,...,J6 (variable number of joints, in degrees)
# - Separators: comma (,)
# - Empty lines are not included
#
# Usage:
# 1. Select a robot routine containing motion statements
# 2. Run the export command
# 3. Choose CSV file location and format
# 4. Points are exported from PTP, LIN, PATH, and CUSTOM motion statements
# -------------------------------------------------------------------------------

from vcCommand import *
import math

# Get Visual Components application instance
app = getApplication()


def OnStart():
    """
    Main entry point for CSV point export functionality.

    Workflow:
    1. Validate active robot routine
    2. Open file dialog for CSV save location
    3. Extract points from robot motion statements
    4. Export data to CSV file with user-selected format
    """
    # Validate that a robot routine is active
    active_routine = app.TeachContext.ActiveRoutine
    if not active_routine:
        print("Error: Please select a robot routine first.")
        return False

    # Open file dialog for CSV save location
    uri = ""
    ok = True
    save_cmd = app.findCommand("dialogSave")
    filefilter = "CSV table (*.csv)|*.csv|All files (*.*)|*.*"
    save_cmd.execute(uri, ok, filefilter)

    # Check if user cancelled file selection
    if not save_cmd.Param_2:
        print("No file selected, aborting command.")
        return False

    # Extract file path
    uri = save_cmd.Param_1
    fileuri = uri[8:]  # Remove 'file://' prefix

    # Ask user for export format
    export_format = get_export_format()
    if export_format is None:
        print("Export cancelled by user")
        return False

    # Extract points from routine
    points_data = extract_points_from_routine(active_routine, export_format)
    if not points_data:
        print("No valid points found in routine to export")
        return False

    # Write data to CSV file
    success = write_csv_file(fileuri, points_data, export_format)

    if success:
        print("Successfully exported %d points to '%s'" % (len(points_data), fileuri))
        return True
    else:
        print("Failed to export points to CSV file")
        return False


def get_export_format():
    """
    Get user preference for export format.

    Returns:
        str: 'position_only' or 'full_pose' or 'joint_angles' or None if cancelled
    """
    # Ask user to select between Position Only or other formats
    first_choice = app.messageBox(
        "Export format options:\n\n"
        + "1. Position Only (X,Y,Z) - Click Cancel\n"
        + "2. Other formats (Full Pose or Joint Angles) - Click OK",
        "Select Export Format",
        VC_MESSAGE_TYPE_QUESTION,
        VC_MESSAGE_BUTTONS_OKCANCEL,
    )

    # If Cancel is clicked, they want Position Only
    if first_choice == VC_MESSAGE_RESULT_CANCEL:
        return "position_only"

    # If OK is clicked, ask them to choose between Full Pose and Joint Angles
    if first_choice == VC_MESSAGE_RESULT_OK:
        second_choice = app.messageBox(
            "Choose export format:\n\n"
            + "1. Full Pose (X,Y,Z,W,P,R) - Click Yes\n"
            + "2. Joint Angles (J1,J2,...) - Click No",
            "Select Format",
            VC_MESSAGE_TYPE_QUESTION,
            VC_MESSAGE_BUTTONS_YESNO,
        )

        if second_choice == VC_MESSAGE_RESULT_YES:
            return "full_pose"
        elif second_choice == VC_MESSAGE_RESULT_NO:
            return "joint_angles"
        else:
            return None

    return None


def extract_points_from_routine(routine, export_format):
    """
    Extract points from robot routine motion statements.

    Args:
        routine: Visual Components routine object
        export_format: Export format ('position_only', 'full_pose', or 'joint_angles')

    Returns:
        list: List of point data tuples
    """
    # Define valid statement types for point extraction
    try:
        ok_types = [
            VC_STATEMENT_PTPMOTION,
            VC_STATEMENT_LINMOTION,
            VC_STATEMENT_CUSTOM,
        ]
        # Try to add path motion if constant exists
        try:
            ok_types.append(VC_STATEMENT_PATH)
        except NameError:
            pass  # PATH constant not available, will detect by position count
    except NameError:
        # Fallback if constants aren't available
        ok_types = [
            VC_STATEMENT_PTPMOTION,
            VC_STATEMENT_LINMOTION,
            VC_STATEMENT_CUSTOM,
        ]

    points_data = []

    for statement in routine.Statements:
        # Check if statement type is valid OR if it has multiple positions (path statement)
        is_valid = statement.Type in ok_types
        has_multiple_positions = (
            hasattr(statement, "Positions")
            and statement.Positions
            and len(statement.Positions) > 1
        )

        if is_valid or has_multiple_positions:
            try:
                # Get number of positions in statement (paths may have multiple positions)
                num_positions = len(statement.Positions) if statement.Positions else 0

                # For path statements, extract all positions
                # For other statements, typically only extract the first position
                # Path statements typically have multiple positions, so check count
                if num_positions > 1:
                    # Likely a path - extract all positions
                    positions_to_extract = num_positions
                else:
                    # Regular motion - extract first position only
                    positions_to_extract = 1 if num_positions > 0 else 0

                for pos_idx in range(positions_to_extract):
                    position = statement.Positions[pos_idx]
                    if not position:
                        continue

                    if export_format == "joint_angles":
                        # Extract joint angles from position (for path, each position may have different joint config)
                        joint_angles = get_joint_angles_from_position(position)
                        if joint_angles:
                            points_data.append(joint_angles)
                    else:
                        # Get transformation matrix
                        transform = position.PositionInReference
                        if not transform:
                            continue

                        # Extract position coordinates
                        x = transform.P.X
                        y = transform.P.Y
                        z = transform.P.Z

                        if export_format == "position_only":
                            points_data.append((x, y, z))
                        else:  # full_pose
                            # Try to get WPR from position object first, then from matrix
                            w, p, r = get_wpr_from_position(position, transform)
                            points_data.append((x, y, z, w, p, r))

            except Exception as e:
                print("Warning: Failed to extract point from statement: %s" % str(e))
                continue

    return points_data


def get_joint_angles_from_position(position):
    """
    Extract joint angles from a position object.

    Args:
        position: Visual Components position object

    Returns:
        tuple: Joint angles in degrees, or None if failed
    """
    try:
        # Method 1: Try to get from position's JointValues
        if hasattr(position, "JointValues") and position.JointValues:
            joint_values = position.JointValues
            if joint_values and len(joint_values) > 0:
                print(
                    "Found joint values via position.JointValues: %d joints"
                    % len(joint_values)
                )
                # Check if values are already in degrees or radians
                joint_angles = []
                for val in joint_values:
                    # If value is > π (3.14) in absolute value, it's likely already in degrees
                    if abs(val) > math.pi:
                        joint_angles.append(val)  # Already in degrees
                    else:
                        joint_angles.append(
                            val * 180.0 / math.pi
                        )  # Convert from radians
                return tuple(joint_angles)

        # Method 2: Try to get from the position frame
        if hasattr(position, "Frame") and position.Frame:
            frame = position.Frame
            if hasattr(frame, "JointValues") and frame.JointValues:
                joint_values = frame.JointValues
                if joint_values and len(joint_values) > 0:
                    print(
                        "Found joint values via frame.JointValues: %d joints"
                        % len(joint_values)
                    )
                    joint_angles = []
                    for val in joint_values:
                        # If value is > π (3.14) in absolute value, it's likely already in degrees
                        if abs(val) > math.pi:
                            joint_angles.append(val)  # Already in degrees
                        else:
                            joint_angles.append(
                                val * 180.0 / math.pi
                            )  # Convert from radians
                    return tuple(joint_angles)

            # Try alternative: get joint configuration from frame
            if hasattr(frame, "JointConfiguration") and frame.JointConfiguration:
                joint_config = frame.JointConfiguration
                if joint_config and len(joint_config) > 0:
                    print(
                        "Found joint configuration via frame.JointConfiguration: %d joints"
                        % len(joint_config)
                    )
                    joint_angles = []
                    for val in joint_config:
                        # Check if value is already in degrees or radians
                        if abs(val) > math.pi:
                            joint_angles.append(val)  # Already in degrees
                        else:
                            joint_angles.append(
                                val * 180.0 / math.pi
                            )  # Convert from radians
                    return tuple(joint_angles)

        return None
    except Exception as e:
        print("Warning: Failed to extract joint angles from position: %s" % str(e))
        return None


def get_joint_angles_from_statement(statement):
    """
    Extract joint angles from a motion statement (for backward compatibility).

    Args:
        statement: Visual Components motion statement object

    Returns:
        tuple: Joint angles in degrees, or None if failed
    """
    try:
        # Get the first position from the statement
        if (
            hasattr(statement, "Positions")
            and statement.Positions
            and len(statement.Positions) > 0
        ):
            return get_joint_angles_from_position(statement.Positions[0])

        return None
    except Exception as e:
        print("Warning: Failed to extract joint angles from statement: %s" % str(e))
        return None


def get_wpr_from_position(position, transform):
    """
    Extract WPR angles from a position object or transformation matrix.
    Tries multiple methods to get the correct WPR values that match Visual Components display.
    
    Args:
        position: Visual Components position object
        transform: vcMatrix transformation matrix
        
    Returns:
        tuple: (W, P, R) angles in degrees
    """
    # Method 1: Try to get WPR directly from position object
    try:
        if hasattr(position, 'WPR'):
            wpr = position.WPR
            if wpr and len(wpr) >= 3:
                # Check if values are in degrees or radians
                w, p, r = wpr[0], wpr[1], wpr[2]
                # If values are small (< 10), they might be in radians
                if abs(w) < 10 and abs(p) < 10 and abs(r) < 10:
                    return (w * 180.0 / math.pi, p * 180.0 / math.pi, r * 180.0 / math.pi)
                return (w, p, r)
    except Exception as e:
        pass
    
    # Method 2: Try to get WPR from position frame
    try:
        if hasattr(position, 'Frame') and position.Frame:
            frame = position.Frame
            if hasattr(frame, 'WPR'):
                wpr = frame.WPR
                if wpr and len(wpr) >= 3:
                    w, p, r = wpr[0], wpr[1], wpr[2]
                    if abs(w) < 10 and abs(p) < 10 and abs(r) < 10:
                        return (w * 180.0 / math.pi, p * 180.0 / math.pi, r * 180.0 / math.pi)
                    return (w, p, r)
    except Exception as e:
        pass
    
    # Method 3: Try matrix getWPR method (if available)
    try:
        if hasattr(transform, 'getWPR'):
            w, p, r = transform.getWPR()
            # getWPR might return radians, check and convert if needed
            if abs(w) < 10 and abs(p) < 10 and abs(r) < 10:
                return (w * 180.0 / math.pi, p * 180.0 / math.pi, r * 180.0 / math.pi)
            return (w, p, r)
    except Exception as e:
        pass
    
    # Method 4: Use manual matrix conversion
    return matrix_to_wpr(transform)


def matrix_to_wpr(matrix):
    """
    Convert transformation matrix to W,P,R angles in degrees.
    Uses Visual Components' ZYX Euler angle convention.

    Args:
        matrix: vcMatrix transformation matrix

    Returns:
        tuple: (W, P, R) angles in degrees
    """
    try:
        # Manual calculation using ZYX Euler angles (Visual Components convention)
        # Extract rotation matrix components
        nx, ny, nz = matrix.N.X, matrix.N.Y, matrix.N.Z
        ox, oy, oz = matrix.O.X, matrix.O.Y, matrix.O.Z
        ax, ay, az = matrix.A.X, matrix.A.Y, matrix.A.Z

        # ZYX Euler angles (WPR) - Visual Components convention:
        # W (Yaw) - rotation around Z axis
        # P (Pitch) - rotation around Y axis  
        # R (Roll) - rotation around X axis
        
        # Calculate P (Pitch) first: P = asin(-nz)
        p_rad = math.asin(-nz)
        p = p_rad * 180.0 / math.pi
        
        # Check for gimbal lock (cos(P) close to zero)
        cos_p = math.cos(p_rad)
        if abs(cos_p) < 1e-6:
            # Gimbal lock case: P = ±90 degrees
            # W and R are not uniquely determined
            w_rad = math.atan2(ox, ax)
            r_rad = 0.0
        else:
            # Normal case: extract W and R using the standard ZYX formula
            w_rad = math.atan2(ny, nx)
            r_rad = math.atan2(oz, az)
        
        w = w_rad * 180.0 / math.pi
        r = r_rad * 180.0 / math.pi

        return (w, p, r)

    except Exception as e:
        print("Warning: Failed to convert matrix to WPR: %s" % str(e))
        import traceback
        traceback.print_exc()
        return (0.0, 0.0, 0.0)


def write_csv_file(filepath, points_data, export_format):
    """
    Write points data to CSV file.

    Args:
        filepath: Path to output CSV file
        points_data: List of point data tuples
        export_format: Export format ('position_only', 'full_pose', or 'joint_angles')

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filepath, "w") as output_file:
            for point in points_data:
                if export_format == "position_only":
                    # Format: X,Y,Z
                    line = "%.6f,%.6f,%.6f" % (point[0], point[1], point[2])
                elif export_format == "full_pose":
                    # Format: X,Y,Z,W,P,R
                    line = "%.6f,%.6f,%.6f,%.6f,%.6f,%.6f" % (
                        point[0],
                        point[1],
                        point[2],
                        point[3],
                        point[4],
                        point[5],
                    )
                else:  # joint_angles
                    # Format: J1,J2,J3,J4,J5,J6 (variable number of joints)
                    # Write all joint angles separated by commas
                    joint_strings = ["%.6f" % angle for angle in point]
                    line = ",".join(joint_strings)

                output_file.write(line + "\n")

        return True

    except IOError as e:
        print("Error writing file: %s" % str(e))
        return False
    except Exception as e:
        print("Error writing CSV data: %s" % str(e))
        return False


addState(None)
