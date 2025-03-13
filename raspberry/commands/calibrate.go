package commands


import (
	"fmt"
	"time"

	"github.com/vistormu/go-berry/comms"
	"github.com/vistormu/go-berry/utils"
	"github.com/vistormu/go-berry/utils/ansi"

	"tactileforce/config"
	"tactileforce/errors"
	"tactileforce/sensors"
)


func Calibrate(args []string) error {
    if len(args) != 0 {
        return errors.New(errors.N_ARGS, 0, len(args))
    }

    config, err := config.LoadConfig()
    if err != nil {
        return errors.New(errors.CONFIG, err)
    }

    return calibrate(config)
}

func calibrate(config *config.Config) error {
    // tactile sensor
    fmt.Println("   |> setting up tactile sensor")
    tactileSensor, err := sensors.NewTactileSensor(
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
    trInit := make([]float64, 4)
    tactileFilter := sensors.NewFilter(
        config.TactileSensor.MedianFilter.Window,
        config.TactileSensor.MedianFilter.PostWindow,
        config.TactileSensor.MedianFilter.Threshold,
        config.TactileSensor.KalmanFilter.ProcessVariance,
        config.TactileSensor.KalmanFilter.MeasurementVariance,
        config.TactileSensor.KalmanFilter.InitialErrorCovariance,
        trInit,
        true,
        false,
        true,
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
        loopStart := time.Now()

        // tactile sensor
        tr, err := tactileSensor.Read()
        if err != nil {
            return err
        }
        tr = tactileFilter.Compute(tr)

        data["time"] = time.Since(programStart).Seconds()
        data["s0"] = tr[0] * 30
        data["s1"] = tr[1] * 30
        data["s2"] = tr[2] * 30
        data["s3"] = tr[3] * 30

        err = client.Send(data)
        if err != nil {
            return err
        }

        loopCounter += 1
        loopTimeAcc += time.Since(loopStart).Seconds() * 1000

        // PRINT
        fmt.Printf("%s%s-> %srunning%s\n   |> time per iteration: %.2f ms\n", 
            ansi.Screen, ansi.Home,
            ansi.Green2, ansi.Reset,
            loopTimeAcc / float64(loopCounter),
        )
    }
    }

    return nil
}
