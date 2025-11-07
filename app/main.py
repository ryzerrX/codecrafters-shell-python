import sys


def main():
    # TODO: Uncomment the code below to pass the first stage
    sys.stdout.write("$ ")
    pass
    error_msg()
    main()

def error_msg():
    user_command = input()
    print(f"{user_command}: command not found")

if __name__ == "__main__":
    main()
