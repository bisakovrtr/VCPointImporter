# -------------------------------------------------------------------------------
# Test Script Command
#
# This command provides a test button to execute a script that prints
# robot program statement information.
# -------------------------------------------------------------------------------

from vcCommand import *

# Get Visual Components application instance
app = getApplication()

# Global variable for test button
test_buttonprop = None


def testScript(arg):
    """
    Execute the test script to print robot program statements.
    
    Args:
        arg: Button click argument (unused)
    """
    teach = app.TeachContext
    robot = teach.ActiveRobot
    
    if not robot:
        app.messageBox(
            "Please select a robot first.",
            "No Robot Selected",
            VC_MESSAGE_TYPE_WARNING,
            VC_MESSAGE_BUTTONS_OK,
        )
        print("Error: No active robot found")
        return
    
    try:
        executors = robot.findBehavioursByType(VC_ROBOTEXECUTOR)
        if not executors or len(executors) == 0:
            app.messageBox(
                "No robot executor found.",
                "Error",
                VC_MESSAGE_TYPE_WARNING,
                VC_MESSAGE_BUTTONS_OK,
            )
            print("Error: No robot executor found")
            return
        
        executor = executors[0]
        main = executor.Program.MainRoutine
        
        for statement in main.Statements:
            if statement.Type == 'Path':
                # Path statements may not have Kind attribute
                name = statement.Name if hasattr(statement, 'Name') else 'Unknown'
                if hasattr(statement, 'Kind'):
                    print(name, statement.Kind)
                else:
                    print(name, statement.Type)
            else:
                name = statement.Name if hasattr(statement, 'Name') else 'Unknown'
                stmt_type = statement.Type if hasattr(statement, 'Type') else 'Unknown'
                print(name, stmt_type)
    except Exception as e:
        print("Error executing test script: %s" % str(e))
        import traceback
        traceback.print_exc()


def test_state():
    """
    Initialize the test command interface with a button.
    
    Returns:
        bool: True if successful, False otherwise
    """
    global test_buttonprop
    
    cmd = getCommand()
    
    # Add test button
    test_buttonprop = cmd.createProperty(VC_BUTTON, "Test")
    test_buttonprop.OnChanged = testScript
    
    # Show property dialog
    executeInActionPanel()
    return True


addState(test_state)

