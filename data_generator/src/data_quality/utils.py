def sample_func():
    pass


def print_colored(message, color_name='OKBLUE'):
    """
    Prints a message to the console in a specified ANSI color.

    :param message: The string message to print.
    :param color_name: The desired color ('HEADER', 'OKBLUE', 'OKCYAN',
                       'OKGREEN', 'WARNING', 'FAIL', 'BOLD', 'UNDERLINE').
                       Defaults to 'OKBLUE'.
    """
    # Define color codes internally
    colors = {
        'HEADER': '\033[95m',
        'OKBLUE': '\033[94m',
        'OKCYAN': '\033[96m',
        'OKGREEN': '\033[92m',
        'WARNING': '\033[93m',
        'FAIL': '\033[91m',
        'ENDC': '\033[0m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
    }

    # Get the start color code, default to the standard ENDC (no color) if invalid name provided
    start_color = colors.get(color_name.upper(), colors['ENDC'])
    end_color = colors['ENDC']

    print(f"{start_color}{message}{end_color}")