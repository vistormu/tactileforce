package commands

import (
    "fmt"
    "tactileforce/errors"
)

var helpFunctions = map[string]func(){
    "run": helpRun,
}

func Help(args []string) error {
    if len(args) > 1 {
        return errors.New(errors.N_ARGS, 1, len(args))
    }

    function, ok := helpFunctions[args[0]]
    if !ok {
        closestMatch := findClosestMatch(args[0], keys(helpFunctions))
        return errors.New(errors.COMMAND, args[0], closestMatch)
    }

    function()

    return nil
}

func helpRun() {
    fmt.Println("Usage: run")
    fmt.Println("Run the program.")
}
