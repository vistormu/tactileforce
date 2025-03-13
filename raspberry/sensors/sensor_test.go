package sensors

import(
    "testing"
    "time"
    "fmt"

    "github.com/vistormu/go-berry/utils"
)


func TestMcp3204(t *testing.T) {
    sensor, err := NewTactileSensor(3.3, 25, 24)
    if err != nil {
        t.Fatal(err)
    }
    
    // variables
    dt := 0.01
    exeTime := 30
    const ClearLastLines = "\033[3A\033[2K\r\033[2K\r\033[2K\r"
    
    // channels
    stopper := utils.NewKbIntListener()
    defer stopper.Stop()

    ticker := time.NewTicker(time.Duration(dt * 1e9))
    defer ticker.Stop()

    programStart := time.Now()

loop:
    for range int(float64(exeTime)/dt) {
    select {
    case <-stopper.Listen():
        fmt.Println("\nReceived interrupt signal. Stopping sensor...")
        break loop

    case <-ticker.C:
        loopStart := time.Now()

        _, err := sensor.Read()
        if err != nil {
            t.Fatal(err)
        }

        fmt.Printf("%s-> \n|> elapsed time: %.0f/%.d s\n   |> time per iteration: %.2f ms", 
            ClearLastLines,
            time.Since(programStart).Seconds(),
            exeTime,
            time.Since(loopStart).Seconds() * 1000,
        )

    }
    }
}


func TestTle493d(t *testing.T) {
    sensor, err := NewTle493e(0x22, 1)
    if err != nil {
        t.Fatal(err)
    }
    
    // variables
    dt := 0.01
    exeTime := 30
    const ClearLastLines = "\033[3A\033[2K\r\033[2K\r\033[2K\r"
    
    // channels
    stopper := utils.NewKbIntListener()
    defer stopper.Stop()

    ticker := time.NewTicker(time.Duration(dt * 1e9))
    defer ticker.Stop()

    // programStart := time.Now()

loop:
    for range int(float64(exeTime)/dt) {
    select {
    case <-stopper.Listen():
        fmt.Println("\nReceived interrupt signal. Stopping sensor...")
        break loop

    case <-ticker.C:
        // loopStart := time.Now()

        // reading, err := sensor.Read()
        _, err := sensor.Read()
        if err != nil {
            t.Fatal(err)
        }

        // fmt.Printf("%s-> %.2f\n|> elapsed time: %.0f/%.d s\n   |> time per iteration: %.2f ms", 
        //     ClearLastLines,
        //     reading,
        //     time.Since(programStart).Seconds(),
        //     exeTime,
        //     time.Since(loopStart).Seconds() * 1000,
        // )

    }
    }
}
