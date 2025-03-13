package errors

import (
    "fmt"
    "strings"
    "reflect"
)


type ErrorType interface {
    String() string
}

type CliError string
type ConfigError string

const (
    E = "\x1b[0m"
    I = "\n   |> "
    F = "\n   |> full error:\n\n%v"
)


const (
    // CLI errors
    N_ARGS      CliError = "wrong number of arguments"+E+I+"expected: %v"+I+"got: %v"
    COMMAND     CliError = "unknown command"+E+I+"got: %v"+I+"did you mean \"\x1b[35m%v\x1b[0m\"?"
    EXTENSION   CliError = "invalid file extension"+E+I+"got: %v"+I+"expected: .prox"
    FLAG        CliError = "unknown flag"+E+I+"got: %v"+I+"did you mean \"\x1b[35m%v\x1b[0m\"?"
    FLAG_VALUE  CliError = "no flag value provided"+E+I+"flag: %v"
    OUTPUT_FLAG CliError = "no output flag provided"+E
    CREATE_FILE CliError = "error creating file"+E+I+"file: %v"
    READ_FILE   CliError = "error reading file"+E+I+"file: %v"

    // Config errors
    CONFIG ConfigError = "error reading config file"+E+F
)


func (e CliError) String() string { return string(e) }
func (e ConfigError) String() string { return string(e) }

var stageMessages = map[reflect.Type]string{
    reflect.TypeOf(CliError("")): "|cli error| ",
    reflect.TypeOf(ConfigError("")): "|config error| ",
}

type Error struct {
    message string
}

func New(errorType ErrorType, args ...any) error {
    stageMessage := stageMessages[reflect.TypeOf(errorType)]
    errorMessage := errorType.String()

    message := "\x1b[31m-> " + stageMessage + errorMessage + "\n"
    n := strings.Count(message, "%v")

    if len(args) != n {
        panic(fmt.Sprintf("expected %v arguments, got %v", n, len(args)))
    }

    message = fmt.Sprintf(message, args...)

    return Error{message}
}

func (e Error) Error() string {
    return e.message
}
