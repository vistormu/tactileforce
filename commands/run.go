package commands

import (
    "fmt"
    "time"
    "math"

    "github.com/vistormu/go-berry/comms"
    "github.com/vistormu/go-berry/utils"

    "tactileforce/sensor"
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
    // force sensor
    fmt.Println("initializing force sensor...")
    botaSensor, err := sensor.New(config.BotaSensor.Port, sensor.DefaultBotaSensorConfig())
    if err != nil {
        return err
    }

    botaSensor.Start()
    time.Sleep(3 * time.Second)
    defer botaSensor.Close()

    // tactile sensor
    fmt.Println("initializing tactile sensor...")
    tactileSensor, err := sensor.NewTactileSensor(
        config.TactileSensor.VRef, 
        config.TactileSensor.ChipSelect,
        config.TactileSensor.LedOnOff,
    )
    defer tactileSensor.Close()

    // client
    fmt.Println("initializing client...")
    client, err := comms.NewUdpClient(config.Client.Ip, config.Client.Port)
    if err != nil {
        return err
    }
    defer client.Close()

    // calibrate
    fmt.Println("calibrating sensors...")
    n := 1000
    tactileReadings := make([]sensor.TactileReading, n)
    botaReadings := make([]sensor.BotaReading, n)
    for i := range n {
        tr, err := tactileSensor.Read()
        if err != nil {
            return err
        }
        tactileReadings[i] = tr
        botaReadings[i] = botaSensor.Read()
        time.Sleep(time.Duration(config.Simulation.Dt))
    }
    
    botaReadingInit := sensor.BotaReadingMean(botaReadings)
    tactileReadingInit := sensor.TactileReadingMean(tactileReadings)

    // filters
    botaFilter := sensor.NewBotaFilter(
        config.BotaSensor.MedianFilter.Window,
        config.BotaSensor.KalmanFilter.ProcessVariance,
        config.BotaSensor.KalmanFilter.MeasurementVariance,
        config.BotaSensor.KalmanFilter.InitialErrorCovariance,
        botaReadingInit,
    )

    tactileFilter := sensor.NewTactileFilter(
        config.TactileSensor.MedianFilter.Window,
        config.TactileSensor.KalmanFilter.ProcessVariance,
        config.TactileSensor.KalmanFilter.MeasurementVariance,
        config.TactileSensor.KalmanFilter.InitialErrorCovariance,
        tactileReadingInit,
    )

    // variables
    data := make(map[string]float64)

    // channels
    stopper := utils.NewKbIntListener()
    defer stopper.Stop()

    ticker := time.NewTicker(time.Duration(config.Simulation.Dt * 1e9))
    defer ticker.Stop()
    
    // loop
    programStart := time.Now()

loop:
    for range int(float64(config.Simulation.ExecutionTime)/config.Simulation.Dt) {
    select {
    case <-stopper.Listen():
        fmt.Println("\nReceived interrupt signal. Stopping sensor...")
        break loop

    case <-ticker.C:
        loopStart := time.Now()

        // force sensor
        botaReading := botaSensor.Read()
        botaReading = botaFilter.Compute(botaReading)
        botaReading = botaReading.Sub(botaReadingInit)

        // tactile sensor
        tactileReading, err := tactileSensor.Read()
        if err != nil {
            return err
        }
        tactileReading = tactileFilter.Compute(tactileReading)
        tactileReading = tactileReading.Sub(tactileReadingInit)


        data["fx"] = float64(botaReading.Fx)
        data["fy"] = float64(botaReading.Fy)
        data["fz"] = float64(botaReading.Fz)
        data["mx"] = float64(botaReading.Mx)
        data["my"] = float64(botaReading.My)
        data["mz"] = float64(botaReading.Mz)
        data["s0v"] = tactileReading.S0v * 100
        data["s1v"] = tactileReading.S1v * 100
        data["s2v"] = tactileReading.S2v * 100
        data["s3v"] = tactileReading.S3v * 100
        data["s0b"] = math.Abs(tactileReading.S0v - tactileReading.S0b) * 100
        data["s1b"] = math.Abs(tactileReading.S1v - tactileReading.S1b) * 100
        data["s2b"] = math.Abs(tactileReading.S2v - tactileReading.S2b) * 100
        data["s3b"] = math.Abs(tactileReading.S3v - tactileReading.S3b) * 100
        data["time"] = time.Since(programStart).Seconds()

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
