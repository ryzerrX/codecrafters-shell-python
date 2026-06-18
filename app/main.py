import sys
import os
import subprocess
import shlex
import contextlib
import readline

HISTORY = []

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

def handle_history(arguments) :
    for index, user_commands in enumerate(HISTORY):
        print(f"{index+1}. {user_commands}")


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
    "cd" : handle_cd,
    "history" : handle_history
}

def history_logic(user_command) :
    global HISTORY
    HISTORY.append(user_command)


def external_cmds_matches(text):
    matches = []
    path_list = os.environ.get("PATH", "").split(os.pathsep)

    for directories in path_list:
        if not os.path.isdir(directories):
            continue

        try:
            for items in  os.listdir(directories):
                if items.startswith(text):
                    full_path = os.path.join(directories, items)
                    if os.access(full_path, os.X_OK):
                        matches.append(items)

        except PermissionError:
            # Some system folders might be restricted
            continue
    return sorted(list(set(matches)))

def completer(text, state):

    # It's better to build the full list of matches only on state 0
    if state == 0:
        builtins = list(COMMAND_MAP.keys())
        
        # Combine built-ins and external commands
        all_possibilities = builtins + external_cmds_matches(text)
        
        # Filter, de-duplicate, and sort
        completer.matches = sorted({
            cmd for cmd in all_possibilities if cmd.startswith(text)
        })

    try:
        # Return the match for the current state
        # Note: We add a space so the user can immediately type arguments
        return completer.matches[state] + " "
    except (IndexError, AttributeError):
        return None

readline.set_completer(completer)           # Register our function with readline
readline.parse_and_bind("tab: complete")    # Tell readline to use the Tab key for completion

def handle_pipelines(parts):

    # 1. Split 'parts' into a list of separate commands
    commands = []
    temp_cmd_bucket = []

    for part in parts:
        if part == '|':
            if not temp_cmd_bucket:
                print("shell: syntax error near unexpected token '|'")
            commands.append(temp_cmd_bucket)
            temp_cmd_bucket = []
        
        else:
            temp_cmd_bucket.append(part)
    
    if temp_cmd_bucket:
        commands.append(temp_cmd_bucket)
    else :
        print("shell: syntax error near unexpected token `|'")
        return
    

    # 2. Execute the Pipeline
    in_fd = 0 # Input File Descriptor - Remembers where the current command should read from. Acts as a memory variable
    pids = []

    for i, cmd_parts in enumerate(commands):
        is_last = (i == len(commands) - 1)

        # Process any > {standard} or < {redirection} symbols for this specific command
        cleaned_parts, out_file , err_file = get_redirection_info(cmd_parts)
        command_name = cleaned_parts[0]
        arguments = cleaned_parts[1:]

        # Create a pipe for the next command(unless this is the last one)
        if not is_last:
            r, w = os.pipe() # os.pipe() gives us r (read end) and w (write end).
        
        pid = os.fork() # Process is split into :
                      # 1) Child - In the Child, pid equals 0. The child enters the {if pid == 0:} block
                      # 2) Parent - In the Parent (your shell), pid is a real number (like 4591). The parent skips to the else: block.

        if pid == 0:

            # 1. Hook up the Pipe Input (The left side of the pipe):
            if in_fd != 0:
                os.dup2(in_fd, 0)   # This tells the OS, "Take my Standard Input (0) and forcefully point it to whatever in_fd is looking at."
                os.close(in_fd)     # We don't need the current in_fd anymore because 0 is doing the job. We close it to keep the FD table clean.
            
            # 2. Hook up the Pipe Output (The right side of the pipe):
            if not is_last:
                os.dup2(w, 1)   # This tells the OS, "Take my Standard Output (1) and forcefully point it to w". Now, if an command prints anything, it goes straight into the new pipe.
                os.close(r)     
                os.close(w)     # The child closes the original pipe variables. It must close r because this child is only writing, not reading from this new pipe. It closes w because FD 1 is already handling the writing.

            # 3. Apply user file redirections (e.g., > or < overrides the pipe)
            if out_file:
                os.dup2(out_file.fileno(), 1)
            if err_file:
                os.dup2(err_file.fileno(), 2)

            # 4. Execute the command (Built-in OR External)
            command_function = COMMAND_MAP.get(command_name)
            
            if command_function:
                # IT'S A BUILT-IN! 
                # Just call the python function. Since FD 1 is redirected to the pipe,
                # any print() inside this function flows into the pipe.
                try:
                    command_function(arguments)
                    os._exit(0) # Crucial: Kill the child after the built-in finishes!
                except Exception as e:
                    print(f"shell: builtin error: {e}", file=sys.stderr)
                    os._exit(1)

            elif check_external_cmd(command_name):
                # IT'S AN EXTERNAL COMMAND!
                try:
                    os.execvp(command_name, cleaned_parts)
                except Exception as e:
                    print(f"shell: {command_name}: {e}", file=sys.stderr)
                    os._exit(1)
            else:
                print(f"shell: {command_name}: command not found", file=sys.stderr)
                os._exit(1)

        else:   # PARENT PROCESS (Your main shell)

            # Every time os.fork() creates a child, the OS assigns it a unique 
            # Process ID (PID). We append this PID to our 'pids' list.
            # Once the main loop finishes setting up all the pipes and children,
            # the parent shell will loop through this list using os.waitpid() 
            # to ensure every command in the pipeline fully completes before 
            # we print the next '$ ' prompt for the user. {This is the use of [pids.append(pid)]} 
            pids.append(pid)    
            
            # Close the read end of the PREVIOUS pipe
            if in_fd != 0:
                os.close(in_fd)
                
            # Set up the read end for the NEXT command
            if not is_last:
                os.close(w) # Parent must close write end!
                in_fd = r
            
            # Close any files opened by get_redirection_info (the child is using them now)
            if out_file: out_file.close()
            if err_file: err_file.close()

    # Wait for all commands in the pipeline to finish
    for pid in pids:
        os.waitpid(pid, 0)

def main():
    while True:

        # take user i/p
        user_command = input("$ ")

        history_logic(user_command)
        # Skip empty input
        if not user_command:
            continue

        # Splitting the Input into a list
        parts = shlex.split(user_command)

        # Handles Command Pipelines
        if '|' in parts:
            handle_pipelines(parts)
            continue

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
