# -------------------------------------------------------------------------------
# CSV Point Import Module for Robot Calibration
#
# This module imports 3D points from CSV files and creates robot motion routines.
# Supports three data formats:
# - Position only: X,Y,Z
# - Full pose: X,Y,Z,W,P,R (W,P,R in degrees)
# - Joint angles: J1,J2,J3,...,J6 (variable number of joints, in degrees)
#
# CSV Format:
# - Position only: X,Y,Z
# - Full pose: X,Y,Z,W,P,R (W,P,R in degrees)
# - Joint angles: J1,J2,J3,...,J6 (in degrees)
# - Separators: comma (,) or semicolon (;)
# - Empty lines are ignored
# -------------------------------------------------------------------------------

from vcCommand import *
import vcMatrix
import os.path
import math

# Get Visual Components application instance
app = getApplication()


def get_import_format():
    """
    Get user preference for import format.

    Returns:
        str: 'coordinates' or 'joint_angles' or None if cancelled
    """
    # Ask user to select import format
    first_choice = app.messageBox(
        "Import format options:\n\n"
        + "1. Coordinates (X,Y,Z or X,Y,Z,W,P,R) - Click OK\n"
        + "2. Joint Angles (J1,J2,...) - Click Cancel",
        "Select Import Format",
        VC_MESSAGE_TYPE_QUESTION,
        VC_MESSAGE_BUTTONS_OKCANCEL,
    )

    if first_choice == VC_MESSAGE_RESULT_OK:
        return "coordinates"
    elif first_choice == VC_MESSAGE_RESULT_CANCEL:
        return "joint_angles"
    else:
        return None


def OnStart():
    """
    Main entry point for CSV point import functionality.

    Workflow:
    1. Validate active robot routine
    2. Open file dialog for CSV selection
    3. Parse CSV data and create robot motion statements
    4. Handle routine overwriting with user confirmation
    """
    # Validate that a robot routine is active
    active_routine = app.TeachContext.ActiveRoutine
    if not active_routine:
        print("Error: Please select a robot first.")
        return False

    # Open file dialog for CSV selection
    uri = ""
    ok = True
    open_cmd = app.findCommand("dialogOpen")
    filefilter = "CSV table (*.csv)|*.csv|All files (*.*)|*.*"
    open_cmd.execute(uri, ok, filefilter)

    # Check if user cancelled file selection
    if not open_cmd.Param_2:
        print("No file selected, aborting command.")
        return False

    # Extract file path and prepare filename
    uri = open_cmd.Param_1
    fileuri = uri[8:]  # Remove 'file://' prefix
    filename = os.path.split(fileuri)[1]
    filename = filename.replace(
        ".", "_"
    )  # Replace dots with underscores for routine name

    # Read and parse CSV file
    try:
        with open(fileuri, "r") as output:
            input_data = output.read()
    except IOError as e:
        print("Error reading file: %s" % str(e))
        return False

    # Ask user for import format
    import_format = get_import_format()
    if import_format is None:
        print("Import cancelled by user")
        return False

    # Get program and check for existing routine
    program = active_routine.Program
    routine = program.findRoutine(filename)

    # Handle routine overwriting
    if routine:
        ret = app.messageBox(
            'Overwriting routine "%s"' % filename,
            "Warning",
            VC_MESSAGE_TYPE_WARNING,
            VC_MESSAGE_BUTTONS_OKCANCEL,
        )
        if ret == VC_MESSAGE_RESULT_CANCEL:
            print("Point importing cancelled by user")
            return False
        program.deleteRoutine(routine)

    # Create new routine for imported points
    routine = program.addRoutine(filename)

    # Parse CSV data and create motion statements
    success = parse_csv_data(input_data, routine, import_format)

    if success:
        app.render()  # Refresh the display
        print("Successfully imported %d points to routine '%s'" % (success, filename))
        return True
    else:
        print("Failed to import any valid points from CSV file")
        return False


def parse_csv_data(input_data, routine, import_format):
    """
    Parse CSV data and create robot motion statements.

    Args:
        input_data (str): Raw CSV file content
        routine: Visual Components routine object to add statements to
        import_format: Import format ('coordinates' or 'joint_angles')

    Returns:
        int: Number of successfully imported points
    """
    lines = input_data.split("\n")
    point_count = 0
    mtx = vcMatrix.new()  # Reuse matrix object for efficiency

    for line_num, line in enumerate(lines, 1):
        # Skip empty lines
        line = line.strip()
        if not line:
            continue

        # Normalize separators (support both comma and semicolon)
        line = line.replace(";", ",")
        cells = line.split(",")

        try:
            if import_format == "joint_angles":
                # Import joint angles
                if len(cells) < 1:
                    print(
                        "Warning: Line %d skipped - insufficient data (need at least one joint)"
                        % line_num
                    )
                    continue

                # Parse all joint angle values (in degrees)
                joint_angles = []
                for cell in cells:
                    val = float(cell.strip())
                    joint_angles.append(val)

                # Keep joint angles in degrees (VC uses degrees for joint values)
                # Note: Forward kinematics may need radians, so we'll convert only for FK

                # Try to get robot controller to set joint configuration
                robot_controller = None
                robot_app = None
                try:
                    # Get the component from the routine's program
                    if hasattr(routine, "Program") and routine.Program:
                        program = routine.Program
                        if hasattr(program, "Component"):
                            robot_controller = program.Component
                            # Get the robot application
                            if robot_controller and hasattr(
                                robot_controller, "Application"
                            ):
                                robot_app = robot_controller.Application
                except Exception as e:
                    print("Debug: Could not get robot controller: %s" % str(e))

                # Create motion statement
                statement = routine.addStatement(VC_STATEMENT_PTPMOTION, point_count)

                # Set joint values
                try:
                    if len(statement.Positions) > 0:
                        position = statement.Positions[0]
                        success = False

                        # Debug: Print available attributes for first point
                        if point_count == 0:
                            print("Debug - Position attributes: %s" % dir(position))
                            if hasattr(position, "Frame"):
                                print("Debug - Has Frame")
                                frame = position.Frame
                                print("Debug - Frame attributes: %s" % dir(frame))
                                if hasattr(frame, "JointValues"):
                                    print(
                                        "Debug - Frame has JointValues: %s"
                                        % frame.JointValues
                                    )
                                if hasattr(frame, "JointConfiguration"):
                                    print("Debug - Frame has JointConfiguration")

                        # First try: Use forward kinematics to calculate Cartesian position
                        if robot_app:
                            try:
                                # Convert to radians only for FK (FK typically expects radians)
                                joint_values_rad_for_fk = [
                                    math.radians(angle) for angle in joint_angles
                                ]

                                if hasattr(robot_app, "FK"):
                                    transform = robot_app.FK(joint_values_rad_for_fk)
                                    if transform:
                                        position.PositionInReference = transform
                                        print(
                                            "Imported joint values for point %d: %d joints (via FK)"
                                            % (point_count, len(joint_angles))
                                        )
                                        success = True
                                elif hasattr(robot_app, "forwardKinematics"):
                                    transform = robot_app.forwardKinematics(
                                        joint_values_rad_for_fk
                                    )
                                    if transform:
                                        position.PositionInReference = transform
                                        print(
                                            "Imported joint values for point %d: %d joints (via forwardKinematics)"
                                            % (point_count, len(joint_angles))
                                        )
                                        success = True
                            except Exception as e:
                                print(
                                    "Warning: FK/forwardKinematics failed: %s" % str(e)
                                )
                                if (
                                    point_count == 0
                                ):  # Print full trace only for first point
                                    import traceback

                                    traceback.print_exc()

                        # Try setting joint values on the position/statement directly
                        if not success:
                            try:
                                # Debug: Print input values
                                print(
                                    "Debug - Input joint angles (degrees): %s"
                                    % joint_angles
                                )

                                # Try using setJoints method first (use degrees)
                                if hasattr(position, "setJoints"):
                                    print(
                                        "Debug - Calling position.setJoints() with degrees"
                                    )
                                    position.setJoints(joint_angles)
                                    success = True
                                    print("Imported via position.setJoints()")

                                # Try to set on Position
                                elif hasattr(position, "JointValues"):
                                    print(
                                        "Debug - Trying to set position.JointValues in degrees"
                                    )
                                    print(
                                        "Debug - position.JointValues length: %d"
                                        % len(position.JointValues)
                                    )
                                    for i, val in enumerate(joint_angles):
                                        if i < len(position.JointValues):
                                            print(
                                                "Debug - Setting position.JointValues[%d] = %f (degrees)"
                                                % (i, val)
                                            )
                                            position.JointValues[i] = val
                                    success = True
                                    print("Imported via position.JointValues")

                                # Try setting on Frame
                                elif hasattr(position, "Frame") and position.Frame:
                                    frame = position.Frame
                                    if (
                                        hasattr(frame, "JointValues")
                                        and frame.JointValues
                                    ):
                                        print(
                                            "Debug - Trying to set frame.JointValues in degrees"
                                        )
                                        for i, val in enumerate(joint_angles):
                                            if i < len(frame.JointValues):
                                                frame.JointValues[i] = val
                                        success = True
                                        print("Imported via frame.JointValues")

                                    elif (
                                        hasattr(frame, "JointConfiguration")
                                        and frame.JointConfiguration
                                    ):
                                        print(
                                            "Debug - Trying to set frame.JointConfiguration in degrees"
                                        )
                                        for i, val in enumerate(joint_angles):
                                            if i < len(frame.JointConfiguration):
                                                frame.JointConfiguration[i] = val
                                        success = True
                                        print("Imported via frame.JointConfiguration")
                            except Exception as e:
                                print(
                                    "Warning: Direct joint value setting failed: %s"
                                    % str(e)
                                )

                        if not success:
                            print(
                                "Warning: Line %d - Could not set joint values for point %d"
                                % (line_num, point_count)
                            )

                except Exception as e:
                    print(
                        "Warning: Line %d - Could not set joint values: %s"
                        % (line_num, str(e))
                    )
                    import traceback

                    traceback.print_exc()

                point_count += 1

            else:  # coordinates
                # Import coordinates (original behavior)
                # Skip lines with insufficient data
                if len(cells) < 3:
                    print(
                        "Warning: Line %d skipped - insufficient data (need at least X,Y,Z)"
                        % line_num
                    )
                    continue

                # Parse position coordinates
                x, y, z = [float(cell.strip()) for cell in cells[:3]]

                # Create motion statement
                statement = routine.addStatement(VC_STATEMENT_PTPMOTION, point_count)

                # Set up transformation matrix
                mtx.identity()
                mtx.translateRel(x, y, z)

                # Parse orientation if available (W,P,R in degrees)
                if len(cells) >= 6:
                    try:
                        w, p, r = [float(cell.strip()) for cell in cells[3:6]]
                        mtx.setWPR(w, p, r)
                    except ValueError:
                        print(
                            "Warning: Line %d - invalid orientation data, using default"
                            % line_num
                        )
                        mtx.rotateRelY(180)  # Default orientation
                else:
                    # Default orientation for position-only data
                    mtx.rotateRelY(180)

                # Apply transformation to statement
                statement.Positions[0].PositionInReference = mtx
                point_count += 1

        except ValueError as e:
            print("Error: Line %d - invalid numeric data: %s" % (line_num, str(e)))
            continue
        except Exception as e:
            print("Error: Line %d - unexpected error: %s" % (line_num, str(e)))
            continue

    return point_count


addState(None)
