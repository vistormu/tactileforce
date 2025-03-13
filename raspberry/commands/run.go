package commands

import (
	"fmt"
	"time"
    "strings"

	"github.com/vistormu/go-berry/comms"
    "github.com/vistormu/go-berry/ml"
	"github.com/vistormu/go-berry/utils"
	"github.com/vistormu/go-berry/utils/ansi"
	"github.com/vistormu/go-berry/utils/num"
	// "github.com/vistormu/go-berry/utils/signal"

	"tactileforce/config"
	"tactileforce/errors"
	"tactileforce/sensors"
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
    botaSensor, err := sensors.New(config.BotaSensor.Port, sensors.DefaultBotaSensorConfig())
    if err != nil {
        return err
    }

    botaSensor.Start()
    time.Sleep(1 * time.Second)
    defer botaSensor.Close()

    // tactile sensor
    fmt.Println("   |> setting up tactile sensor")
    tactileSensor, err := sensors.NewTactileSensor(
        config.TactileSensor.VRef, 
        config.TactileSensor.ChipSelect,
        config.TactileSensor.LedOnOff,
    )
    defer tactileSensor.Close()

    // model
    fmt.Println("   |> setting up model")
    var model ml.Model
    if config.Model.Local {
        model, err = ml.NewLocalModel(
            config.Model.Path,
            config.Model.NInputs,
            config.Model.NOutputs,
        )
    } else {
        model, _ = ml.NewRemoteModel(
            config.Client.Ip,
            config.Client.Port,
            "predict",
            "output",
            []string{"s0", "s1", "s2", "s3"},
        )
    }
    if err != nil {
        return err
    }
    defer model.Close()

    // modelFilter := signal.NewMultiMedianFilter[float32](config.TactileSensor.MedianFilter.Window, 4)

    // client
    fmt.Println("   |> setting up client")
    client, err := comms.NewUdpClient(config.Client.Ip, config.Client.Port)
    if err != nil {
        return err
    }
    defer client.Close()

    // filters
    botaReadingInit := make([]float64, 6)
    botaFilter := sensors.NewFilter(
        config.BotaSensor.MedianFilter.Window,
        config.BotaSensor.MedianFilter.PostWindow,
        float64(config.BotaSensor.MedianFilter.Threshold),
        config.BotaSensor.KalmanFilter.ProcessVariance,
        config.BotaSensor.KalmanFilter.MeasurementVariance,
        config.BotaSensor.KalmanFilter.InitialErrorCovariance,
        botaReadingInit,
        false,
        false,
        true,
    )

    tactileReadingInit := make([]float64, 4)
    tactileFilter := sensors.NewFilter(
        config.TactileSensor.MedianFilter.Window,
        config.TactileSensor.MedianFilter.PostWindow,
        config.TactileSensor.MedianFilter.Threshold,
        config.TactileSensor.KalmanFilter.ProcessVariance,
        config.TactileSensor.KalmanFilter.MeasurementVariance,
        config.TactileSensor.KalmanFilter.InitialErrorCovariance,
        tactileReadingInit,
        true,
        false,
        true,
    )

    // channels
    stopper := utils.NewKbIntListener()
    defer stopper.Stop()

    ticker := time.NewTicker(time.Duration(config.Simulation.Dt * 1e9))
    defer ticker.Stop()


    
    // variables
    n := int(float64(config.Simulation.CalibrationTime) / config.Simulation.Dt)
    tactileReadings := utils.NewQueue[[]float64](n)
    botaReadings := utils.NewQueue[[]float64](n)

    loopCounter := 0
    loopTimeAcc := 0.0
    programStart := time.Now()

    loop:
    for {
    select {
    case <-stopper.Listen():
        break loop

    case <-ticker.C:
        simulationEnded := int(time.Since(programStart).Seconds()) >= config.Simulation.ExecutionTime
        calibrated := botaReadings.Full() && tactileReadings.Full()

        // program ended
        if simulationEnded && calibrated {
            var answer string
            fmt.Printf("%s%s-> %sfinished%s\n   |> elapsed time: %.d/%.d s\n   |> repeat? [y/n]: ", 
                ansi.Screen, ansi.Home,
                ansi.Yellow2, ansi.Reset,
                config.Simulation.ExecutionTime,
                config.Simulation.ExecutionTime,
            )
            fmt.Scan(&answer)

            if strings.TrimSpace(answer) == "n" {
                break loop
            }

            loopCounter = 0
            loopTimeAcc = 0.0
            botaReadings.Clear()
            tactileReadings.Clear()
            botaFilter.Reset(make([]float64, 6))
            tactileFilter.Reset(make([]float64, 4))
            programStart = time.Now()

            continue loop
        }

        // calibration
        if !calibrated {
            tr, err := tactileSensor.Read()
            if err != nil {
                return err
            }
            tactileReadings.Append(tactileFilter.Compute(tr))
            botaReadings.Append(botaFilter.Compute(botaSensor.Read()))

            fmt.Printf("%s%s-> %scalibrating%s\n   |> elapsed time: %.0f/%.d s\n", 
                ansi.Screen, ansi.Home,
                ansi.Cyan, ansi.Reset,
                time.Since(programStart).Seconds(),
                config.Simulation.CalibrationTime,
            )

            if !tactileReadings.Full() && !botaReadings.Full() {
                continue
            }

            from := int(float64(config.Simulation.CalibrationTrim)/100*float64(n))
            botaReadingInit = num.MultiMean(botaReadings.Slice(from, n-1))
            tactileReadingInit = num.MultiMean(tactileReadings.Slice(from, n-1))

            botaFilter.Reset(botaReadingInit)
            tactileFilter.Reset(tactileReadingInit)

            programStart = time.Now()
        }
        
        loopStart := time.Now()

        // force sensor
        br := botaSensor.Read()
        br = botaFilter.Compute(br)

        // tactile sensor
        tr, err := tactileSensor.Read()
        if err != nil {
            return err
        }
        tr = tactileFilter.Compute(tr)

        // model
        // modelOutput, err := model.Compute(tr)
        // if err != nil {
        //     return err
        // }
        // modelOutput = modelFilter.Compute(modelOutput)

        data := map[string]float64 {
            "time": time.Since(programStart).Seconds(),

            "fx": br[0],
            "fy": br[1],
            "fz": br[2],
            "mx": br[3],
            "my": br[4],
            "mz": br[5],

            "s0": tr[0] * 100,
            "s1": tr[1] * 100,
            "s2": tr[2] * 100,
            "s3": tr[3] * 100,
        }

        err = client.Send(data)
        if err != nil {
            return err
        }

        loopCounter += 1
        loopTimeAcc += time.Since(loopStart).Seconds() * 1000

        // PRINT
        fmt.Printf("%s%s-> %srunning%s\n   |> elapsed time: %.0f/%.d s\n   |> time per iteration: %.2f ms (%.2f)\n", 
            ansi.Screen, ansi.Home,
            ansi.Green2, ansi.Reset,
            time.Since(programStart).Seconds(),
            config.Simulation.ExecutionTime,
            loopTimeAcc / float64(loopCounter),
            time.Since(loopStart).Seconds() * 1000,
        )
    }
    }

    return nil
}
