import sys
import os
import subprocess
import shlex
import contextlib

def get_redirection_info(parts) : 
    """
    Checks for redirection operators.
    Returns (cleaned_parts, file_handle)
    """

    stdout_handle = None
    stderr_handle = None

    cleaned_parts = parts[:]

    operators = [">", "1>"] # Defining Operators

    if "2>" in cleaned_parts :
        idx = cleaned_parts.index("2>")
        filename = cleaned_parts[idx + 1]
        stderr_handle = open(filename, "w")

        cleaned_parts = cleaned_parts[:idx] + cleaned_parts[idx+2:]

    for op in operators :
        if op in cleaned_parts :
            idx = cleaned_parts.index(op) 
            filename = cleaned_parts[idx + 1] 
            stdout_handle = open(filename, "w") # Open for writing (creates if missing, overwrites if exists)

            cleaned_parts = cleaned_parts[:idx] + cleaned_parts[idx+2:] # Remove the operator and the filename from the parts list
                                                            # e.g. ['echo', 'hi', '>', 'out.txt'] -> ['echo', 'hi']
            break

    return cleaned_parts, stdout_handle, stderr_handle

def handle_echo(arguments):
    print(" ".join(arguments))

def handle_exit(arguments):
    """
    Weird Logic for some reson
    """

    if '0' in arguments:
        # print("Exiting with status 0 (success)")
        sys.exit(0)
    elif '1' in arguments:
        # print("Exiting with status 1 (error)")
        sys.exit(1)
    else:
        # print("invalid argument")
        sys.exit(0)

def handle_type(arguments):
        # If no argument was given
        if not arguments:
            return
        
        arg = arguments[0]

        # Checking for builtin command
        if arg in COMMAND_MAP:
            print(f"{arg} is a shell builtin")
            return
        
        # Get PATH 
        path_string = os.environ.get("PATH")

        # If PATH is not given
        if not path_string:
            print(f"{arg}: not found")
            return
        
        directories = path_string.split(os.pathsep) # Forming a list of possible directories, We can use {os.path.split} instead

        # Searching the PATH directories to check is the file exists and is executable
        found = False
        for directory in directories:
            full_path = os.path.join(directory, arg)

            if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                print(f"{arg} is {full_path}")
                found = True
                break
        
        # If the file is still not found
        if not found:
            print(f"{arg}: not found")

def handle_pwd(_):
    current_dir = os.getcwd()
    print(current_dir)

def handle_cd(argumnets):

    path = os.path.expanduser("".join(argumnets))

    if os.path.exists(path):
        os.chdir(path)
    else:
        print(f"cd: {path}: No such file or directory")

def error_msg(command_name):
    print(f"{command_name}: command not found")

def check_external_cmd(command_name):
    # Get PATH 
    path_string = os.environ.get("PATH")

    # If PATH is not given
    if not path_string:
        error_msg(command_name)
        return
        
    directories = path_string.split(os.pathsep) # Forming a list of possible directories

    # Searching the PATH directories to check is the file exists and is executable
    found = False
    for directory in directories:
        full_path = os.path.join(directory, command_name)

        if os.path.exists(full_path) and os.access(full_path, os.X_OK):
            found = True
            break
    return found

COMMAND_MAP = {
    "echo": handle_echo,
    "exit": handle_exit,
    "type": handle_type,
    "pwd" : handle_pwd,
    "cd" : handle_cd
}

def main():
    while True:
        # TODO: Uncomment the code below to pass the first stage
        sys.stdout.write("$ ")
        pass

        # take user i/p
        user_command = input()

        # Skip empty input
        if not user_command:
            continue

        # Splitting the Input into a list
        parts = shlex.split(user_command)

        cleaned_parts, out_file , err_file = get_redirection_info(parts)

        command_name = cleaned_parts[0]
        arguments = cleaned_parts[1:]

        # Finding the Command Function
        command_function = COMMAND_MAP.get(command_name)

        if command_function:
            with contextlib.redirect_stdout(out_file or sys.stdout), contextlib.redirect_stderr(err_file or sys.stderr) :
                command_function(arguments)

        elif check_external_cmd(command_name):
            subprocess.run(cleaned_parts, stdout=out_file, stderr=err_file)
            
        else:
            error_msg(command_name)

        for handle in [out_file, err_file] :
            if handle :
                handle.close()

if __name__ == "__main__":
    main()
