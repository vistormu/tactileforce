package commands

import (
    "fmt"
    "time"

    "github.com/vistormu/goraspio/client"
    "github.com/vistormu/goraspio/utils"

    "tactileforce/sensor"
    "tactileforce/filter"
    "tactileforce/errors"
    "tactileforce/config"
)

const ClearLastLines = "\033[3A\033[2K\r\033[2K\r\033[2K\r"

func Run(args []string) error {
    if len(args) != 0 {
        return errors.New(errors.N_ARGS, 0, len(args))
    }

    config, err := config.LoadConfig()
    if err != nil {
        return errors.New(errors.CONFIG, err)
    }

    return run(config)
}

func run(config *config.Config) error {
    // sensor
    botaSensor, err := sensor.New(config.BotaSensor.Port, sensor.DefaultBotaSensorConfig())
    if err != nil {
        return err
    }

    botaSensor.Start()
    time.Sleep(3 * time.Second)
    defer botaSensor.Close()

    initialReading := botaSensor.Read()

    // client
    client, err := client.New(config.Client.Ip, config.Client.Port)
    if err != nil {
        return err
    }
    defer client.Close()

    // filter
    filter := filter.NewFilter(
        config.BotaSensor.MedianFilter.Window,
        config.BotaSensor.KalmanFilter.ProcessVariance,
        config.BotaSensor.KalmanFilter.MeasurementVariance,
        config.BotaSensor.KalmanFilter.InitialErrorCovariance,
        initialReading,
    )

    // variables
    data := make(map[string]float32)

    // channels
    stopper := utils.NewGracefulStopper()

    ticker := time.NewTicker(time.Duration(config.Simulation.Dt * 1e9))
    defer ticker.Stop()

    programStart := time.Now()

loop:
    for range int(float64(config.Simulation.ExecutionTime)/config.Simulation.Dt) {
    select {
    case <-stopper.Listen():
        fmt.Println("Received interrupt signal. Stopping sensor...")
        break loop

    case <-ticker.C:
        loopStart := time.Now()

        // Get the latest reading
        reading := filter.Compute(botaSensor.Read()).Sub(initialReading)

        data["fx"] = reading.Fx
        data["fy"] = reading.Fy
        data["fz"] = reading.Fz
        data["mx"] = reading.Mx
        data["my"] = reading.My
        data["mz"] = reading.Mz
        data["temperature"] = reading.Temperature
        // data["time"] = reading.timestamp
        data["time"] = float32(time.Since(programStart).Seconds())

        err = client.Send(data)
        if err != nil {
            return err
        }

        // PRINT
        fmt.Printf("%s-> running experiment\n   |> elapsed time: %.0f/%.d s\n   |> time per iteration: %.2f ms", 
            ClearLastLines,
            time.Since(programStart).Seconds(),
            config.Simulation.ExecutionTime,
            time.Since(loopStart).Seconds() * 1000,
        )
    }
    }

    return nil
}
