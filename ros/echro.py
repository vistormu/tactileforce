import sys

id_to_ansi = {
    # cursor
    "home": "\x1b[H",  # ]
    "up": "\x1b[A",  # ]
    "down": "\x1b[B",  # ]
    "right": "\x1b[C",  # ]
    "left": "\x1b[D",  # ]
    "start": "\r",  # ]

    # clear
    "screen-end": "\x1b[0J",  # ]
    "screen-start": "\x1b[1J",  # ]
    "screen": "\x1b[2J",  # ]
    "line-end": "\x1b[0K",  # ]
    "line-start": "\x1b[1K",  # ]
    "line": "\x1b[2K",  # ]

    # style
    "bold": "\x1b[1m",  # ]
    "dim": "\x1b[2m",  # ]
    "italic": "\x1b[3m",  # ]
    "underline": "\x1b[4m",  # ]
    "blink": "\x1b[5m",  # ]
    "reverse": "\x1b[7m",  # ]
    "hidden": "\x1b[8m",  # ]
    "strike": "\x1b[9m",  # ]

    # color
    "reset": "\x1b[0m",  # ]
    "black": "\x1b[30m",  # ]
    "red": "\x1b[31m",  # ]
    "green": "\x1b[32m",  # ]
    "yellow": "\x1b[33m",  # ]
    "blue": "\x1b[34m",  # ]
    "magenta": "\x1b[35m",  # ]
    "cyan": "\x1b[36m",  # ]
    "white": "\x1b[37m",  # ]
    "black2": "\x1b[90m",  # ]
    "red2": "\x1b[91m",  # ]
    "green2": "\x1b[92m",  # ]
    "yellow2": "\x1b[93m",  # ]
    "blue2": "\x1b[94m",  # ]
    "magenta2": "\x1b[95m",  # ]
    "cyan2": "\x1b[96m",  # ]
    "white2": "\x1b[97m",  # ]

    # background
    "bg-black": "\x1b[40m",  # ]
    "bg-red": "\x1b[41m",  # ]
    "bg-green": "\x1b[42m",  # ]
    "bg-yellow": "\x1b[43m",  # ]
    "bg-blue": "\x1b[44m",  # ]
    "bg-magenta": "\x1b[45m",  # ]
    "bg-cyan": "\x1b[46m",  # ]
    "bg-white": "\x1b[47m",  # ]
    "bg-black2": "\x1b[100m",  # ]
    "bg-red2": "\x1b[101m",  # ]
    "bg-green2": "\x1b[102m",  # ]
    "bg-yellow2": "\x1b[103m",  # ]
    "bg-blue2": "\x1b[104m",  # ]
    "bg-magenta2": "\x1b[105m",  # ]
    "bg-cyan2": "\x1b[106m",  # ]
    "bg-white2": "\x1b[107m",  # ]
}


def echo(*msg: str, pipeline: str) -> None:
    print_msg = ""
    for cmd in pipeline.split(","):
        cmd = cmd.strip()
        if cmd.isdigit():
            print_msg += msg[int(cmd)]
            continue

        ansi = id_to_ansi.get(cmd)
        if ansi:
            print_msg += ansi

    sys.stdout.write(print_msg)
    sys.stdout.flush()


if __name__ == "__main__":
    import time
    import random

    sys.stdout.write("hello\n")
    sys.stdout.flush()

    time.sleep(1.0)

    for i in range(101):
        first = random.randint(0, 100)
        second = random.choice(["red", "green", "yellow", "blue", "magenta", "cyan"])
        third = i

        echo(
            "-> printing a cool message\n",
            f"   |> first: {first}\n",
            f"   |> second: {second}\n",
            f"   |> third: {third}",
            pipeline=f"""line,start,up,line,up,line,
            red,bold,0,reset,
            blue,1,reset,
            {second},2,reset,
            green,3,reset""",
        )

        time.sleep(1.0)
