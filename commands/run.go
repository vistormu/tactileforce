package commands

import (
	"fmt"
	// "math"
	"time"

	"github.com/vistormu/go-berry/comms"
	"github.com/vistormu/go-berry/utils"

	"tactileforce/ansi"
	"tactileforce/config"
	"tactileforce/errors"
	"tactileforce/sensor"
)


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
    fmt.Printf("%s%s-> %sinitializing program%s\n", 
        ansi.Screen, ansi.Home,
        ansi.Cyan2, ansi.Reset,
    )
    fmt.Println("   |> setting up force-torque sensor")
    botaSensor, err := sensor.New(config.BotaSensor.Port, sensor.DefaultBotaSensorConfig())
    if err != nil {
        return err
    }

    botaSensor.Start()
    time.Sleep(1 * time.Second)
    defer botaSensor.Close()

    // tactile sensor
    fmt.Println("   |> setting up tactile sensor")
    tactileSensor, err := sensor.NewTactileSensor(
        config.TactileSensor.VRef, 
        config.TactileSensor.ChipSelect,
        config.TactileSensor.LedOnOff,
    )
    defer tactileSensor.Close()

    // client
    fmt.Println("   |> setting up client")
    client, err := comms.NewUdpClient(config.Client.Ip, config.Client.Port)
    if err != nil {
        return err
    }
    defer client.Close()

    // calibrate
    fmt.Println("   |> calibrating sensors")
    botaFilter := sensor.NewBotaFilter(
        config.BotaSensor.MedianFilter.Window,
        config.BotaSensor.KalmanFilter.ProcessVariance,
        config.BotaSensor.KalmanFilter.MeasurementVariance,
        config.BotaSensor.KalmanFilter.InitialErrorCovariance,
        sensor.BotaReading{},
    )

    tactileFilter := sensor.NewTactileFilter(
        config.TactileSensor.MedianFilter.Window,
        config.TactileSensor.KalmanFilter.ProcessVariance,
        config.TactileSensor.KalmanFilter.MeasurementVariance,
        config.TactileSensor.KalmanFilter.InitialErrorCovariance,
        sensor.TactileReading{},
    )

    n := 1000
    tactileReadings := make([]sensor.TactileReading, n)
    botaReadings := make([]sensor.BotaReading, n)
    for i := range n {
        tr, err := tactileSensor.Read()
        if err != nil {
            return err
        }
        tactileReadings[i] = tactileFilter.Compute(tr)
        botaReadings[i] = botaFilter.Compute(botaSensor.Read())
        time.Sleep(time.Duration(config.Simulation.Dt))
    }
    
    botaReadingInit := sensor.BotaReadingMean(botaReadings[200:])
    tactileReadingInit := sensor.TactileReadingMean(tactileReadings[200:])

    // filters
    botaFilter = sensor.NewBotaFilter(
        config.BotaSensor.MedianFilter.Window,
        config.BotaSensor.KalmanFilter.ProcessVariance,
        config.BotaSensor.KalmanFilter.MeasurementVariance,
        config.BotaSensor.KalmanFilter.InitialErrorCovariance,
        botaReadingInit,
    )

    tactileFilter = sensor.NewTactileFilter(
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
    loopCounter := 0
    loopTimeAcc := 0.0

    loop:
    for {
    select {
    case <-stopper.Listen():
        fmt.Printf("%s%s-> %sfinished%s\n   |> keyboard interrupt\n", 
            ansi.Screen, ansi.Home,
            ansi.Yellow2, ansi.Reset,
        )
        break loop

    case <-ticker.C:
        if int(time.Since(programStart).Seconds()) >= config.Simulation.ExecutionTime {
            fmt.Printf("%s%s-> %sfinished%s\n   |> elapsed time: %.d/%.d s\n   |> continue? [y/n]: ", 
                ansi.Screen, ansi.Home,
                ansi.Yellow2, ansi.Reset,
                config.Simulation.ExecutionTime,
                config.Simulation.ExecutionTime,
            )
            var answer string
            fmt.Scan(&answer)

            if answer == "n" {
                break loop
            }

            programStart = time.Now()
            loopCounter = 0
            loopTimeAcc = 0.0
            continue loop
        }

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
        tactileReadingRel := tactileReading.Sub(tactileReadingInit)


        data["fx"] = float64(botaReading.Fx)
        data["fy"] = float64(botaReading.Fy)
        data["fz"] = float64(botaReading.Fz)
        data["mx"] = float64(botaReading.Mx)
        data["my"] = float64(botaReading.My)
        data["mz"] = float64(botaReading.Mz)
        data["s0"] = tactileReadingRel.S0v * 100
        data["s1"] = tactileReadingRel.S1v * 100
        data["s2"] = tactileReadingRel.S2v * 100
        data["s3"] = tactileReadingRel.S3v * 100
        // data["s0b"] = math.Abs(tactileReading.S0v - tactileReading.S0b) * 4600
        // data["s1b"] = math.Abs(tactileReading.S1v - tactileReading.S1b) * 4600
        // data["s2b"] = math.Abs(tactileReading.S2v - tactileReading.S2b) * 4600
        // data["s3b"] = math.Abs(tactileReading.S3v - tactileReading.S3b) * 4600
        data["time"] = time.Since(programStart).Seconds()

        err = client.Send(data)
        if err != nil {
            return err
        }

        loopCounter += 1
        loopTimeAcc += time.Since(loopStart).Seconds() * 1000

        // PRINT
        fmt.Printf("%s%s-> %srunning%s\n   |> elapsed time: %.0f/%.d s\n   |> time per iteration: %.2f ms\n", 
            ansi.Screen, ansi.Home,
            ansi.Green2, ansi.Reset,
            time.Since(programStart).Seconds(),
            config.Simulation.ExecutionTime,
            loopTimeAcc / float64(loopCounter),
        )
    }
    }

    return nil
}
