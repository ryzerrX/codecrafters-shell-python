import sys


def main():
    while True:
        # TODO: Uncomment the code below to pass the first stage
        sys.stdout.write("$ ")
        pass
        user_command = input()
        if user_command == "exit 0" or user_command == "exit 1":
            break
        else:
            error_msg(user_command)


def error_msg(user_command):
    print(f"{user_command}: command not found")

if __name__ == "__main__":
    main()
