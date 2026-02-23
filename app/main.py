import sys
import os
import subprocess
import shlex
import contextlib
import readline

def get_redirection_info(parts) : 
    """
    Checks for redirection operators.
    Returns (cleaned_parts, file_handle)
    """

    stdout_handle = None
    stderr_handle = None

    cleaned_parts = parts[:]

    # Defining Operators
    operators = {
        ">":   {"mode": "w", "stream": "stdout"},
        "1>":  {"mode": "w", "stream": "stdout"},
        ">>":  {"mode": "a", "stream": "stdout"},
        "1>>": {"mode": "a", "stream": "stdout"},
        "2>":  {"mode": "w", "stream": "stderr"},
        "2>>": {"mode": "a", "stream": "stderr"}
    }
    
    for op, rule in operators.items() :
        while op in cleaned_parts :
            idx = cleaned_parts.index(op) 
            filename = cleaned_parts[idx + 1] 

            mode = rule["mode"]
            stream = rule["stream"]

            if stream == "stdout" :
                stdout_handle = open(filename, mode) # Open for writing (creates if missing, overwrites if exists)
                
                cleaned_parts = cleaned_parts[:idx] + cleaned_parts[idx+2:] # Remove the operator and the filename from the parts list
                                                                            # e.g. ['echo', 'hi', '>', 'out.txt'] -> ['echo', 'hi']

            if stream == "stderr" :
               stderr_handle = open(filename, mode)

               cleaned_parts = cleaned_parts[:idx] + cleaned_parts[idx+2:] 

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

def external_cmds_matches(text):
    matches = []
    path = os.environ.get("PATH").split(os.pathsep)

    for directories in path:
        
        for items in  os.listdir(directories):
            if items.startswith(text):
                full_path = os.path.join(path, items)
                # if os.access(full_path, os.X_OK):
                matches.append(items)
    
    return sorted(list(set(matches)))

        

def completer(text, state):

    builtins = list(COMMAND_MAP.keys())

    # 1. Filter the COMMANDS list. Find all words that start with 'text'.
    #    (Hint: Python string methods like .startswith() are great here).
    
    matches = []
    for cmd in builtins:
        if cmd.startswith(text):
            matches.append(cmd + " ")
    matches += external_cmds_matches(text)

    # 2. Try to return the item from the filtered list at index 'state'.
    # 3. If 'state' is larger than your filtered list, catch the error 
    #    and return None to tell readline to stop.

    return matches[state] if state < len(matches) else None



readline.set_completer(completer)           # Register our function with readline
readline.parse_and_bind("tab: complete")    # Tell readline to use the Tab key for completion


def main():
    while True:

        # take user i/p
        user_command = input("$ ")

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
