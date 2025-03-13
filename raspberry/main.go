package main

import (
    "os"
    "tactileforce/commands"
)

func main() {
    commands.Execute(os.Args[1:])
}
