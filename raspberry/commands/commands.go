package commands

import (
    "os"
    "fmt"
    "tactileforce/errors"
)

type CommnadFunc func(args []string) error
var commands = map[string]CommnadFunc{
    "run": Run,
    "calibrate": Calibrate,
    "help": Help,
}

func Execute(args []string) {
    err := execute(args)
    if err != nil {
        fmt.Println(err.Error())
        os.Exit(1)
    }
}

func execute(args []string) error {
    if len(args) < 1 {
        return errors.New(errors.N_ARGS, "at least one", len(args)-1)
    }

    command, ok := commands[args[0]]
    if !ok {
        closestMatch := findClosestMatch(args[0], keys(commands))
        return errors.New(errors.COMMAND, args[0], closestMatch)
    }

    return command(args[1:])
}
