import sys

def handle_echo(arguments):
    print(" ".join(arguments))

def handle_exit(arguments):
    if '0' in arguments:
        # print("Exiting with status 0 (success)")
        sys.exit(0)
    elif '1' in arguments:
        # print("Exiting with status 1 (error)")
        sys.exit(1)
    else:
        print("invalid argument")

def error_msg(command_name):
    print(f"{command_name}: command not found")

COMMAND_MAP = {
    "echo": handle_echo,
    "exit": handle_exit
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
        parts = user_command.split()
        command_name = parts[0]
        arguments = parts[1:]

        # Finding the Command Function
        command_function = COMMAND_MAP.get(command_name)

        if command_function:
            command_function(arguments)
        else:
            error_msg(command_name)


if __name__ == "__main__":
    main()
