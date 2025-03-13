package sensors

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"sync"
	"time"
    "math"

	"github.com/sigurn/crc16"
	"go.bug.st/serial"
)

// =======
// READING
// =======
type BotaReading struct {
    Fx          float32
    Fy          float32
    Fz          float32
    Mx          float32
    My          float32
    Mz          float32
    Timestamp   float32
    Temperature float32
}

// ======
// CONFIG
// ======
type BotaSensorConfig struct {
    BaudRate          int
    SincLength        int
    ChopEnable        int
    FastEnable        int
    FirDisable        int
    TempCompensation  int // 0: Disabled, 1: Enabled
    UseCalibration    int // 1: calibration matrix active, 0: raw measurements
    DataFormat        int // 0: binary, 1: CSV
    BaudRateConfig    int // 0: 9600, 1: 57600, 2: 115200, 3: 230400, 4: 460800
    FrameHeader       byte
}

func DefaultBotaSensorConfig() BotaSensorConfig {
    return BotaSensorConfig{
        BaudRate:         460800,
        SincLength:       512,
        ChopEnable:       0,
        FastEnable:       0,
        FirDisable:       1,
        TempCompensation: 0,
        UseCalibration:   1,
        DataFormat:       0,
        BaudRateConfig:   4,
        FrameHeader:      0xAA,
    }
}


// ======
// SENSOR
// ======
type BotaSensor struct {
    port      serial.Port
    header    byte
    status    uint16
    reading   BotaReading
    stopCh    chan struct{}
    waitGroup sync.WaitGroup
    mux       sync.RWMutex // to guard reading/status
    timeStep  float64
}

func New(portName string, config BotaSensorConfig) (*BotaSensor, error) {
    mode := &serial.Mode{
        BaudRate: config.BaudRate,
    }

    port, err := serial.Open(portName, mode)
    if err != nil {
        return nil, fmt.Errorf("could not open port %s: %w", portName, err)
    }

    sensor := &BotaSensor{
        port:     port,
        header:   0xAA,
        reading:  BotaReading{},
        stopCh:   make(chan struct{}),
        waitGroup: sync.WaitGroup{},
        mux:      sync.RWMutex{},
    }

    err = sensor.setup(config)
    if err != nil {
        return nil, fmt.Errorf("failed to setup sensor: %w", err)
    }

    return sensor, nil
}

func (b *BotaSensor) setup(config BotaSensorConfig) error {
    var err error

    // 1) Wait for "App Init" output from sensor
    err = readUntil(b.port, []byte("App Init"), 10*time.Second)
    if err != nil {
        return fmt.Errorf("sensor not streaming or timed out waiting for 'App Init': %w", err)
    }

    // Clear buffers
    b.port.ResetInputBuffer()
    b.port.ResetOutputBuffer()

    // 2) Go to CONFIG mode
    err = writeAndCheck(b.port, "C", []byte("r,0,C,0"), 2*time.Second)
    if err != nil {
        return fmt.Errorf("failed to go to CONFIG mode: %w", err)
    }

    // 3) Communication setup
    commSetup := fmt.Sprintf("c,%d,%d,%d,%d",
        config.TempCompensation,
        config.UseCalibration,
        config.DataFormat,
        config.BaudRateConfig,
    )
    err = writeAndCheck(b.port, commSetup, []byte("r,0,c,0"), 2*time.Second)
    if err != nil {
        return fmt.Errorf("failed to set communication setup: %w", err)
    }

    // 4) Filter setup
    filterSetup := fmt.Sprintf("f,%d,%d,%d,%d",
        config.SincLength,
        config.ChopEnable,
        config.FastEnable,
        config.FirDisable,
    )
    err = writeAndCheck(b.port, filterSetup, []byte("r,0,f,0"), 2*time.Second)
    if err != nil {
        return fmt.Errorf("failed to set filter setup: %w", err)
    }

    // 5) Go to RUN mode
    err = writeAndCheck(b.port, "R", []byte("r,0,R,0"), 2*time.Second)
    if err != nil {
        return fmt.Errorf("failed to go to RUN mode: %w", err)
    }

    return nil
}

func readUntil(port serial.Port, terminator []byte, timeout time.Duration) error {
    deadline := time.Now().Add(timeout)
    buf := make([]byte, 1)
    var collected []byte

    for {
        if time.Now().After(deadline) {
            return fmt.Errorf("timeout while waiting for terminator '%s'", terminator)
        }
        n, err := port.Read(buf)
        if err != nil || n == 0 {
            // Sleep a bit and try again
            time.Sleep(10 * time.Millisecond)
            continue
        }
        collected = append(collected, buf[0])
        if len(collected) >= len(terminator) {
            if string(collected[len(collected)-len(terminator):]) == string(terminator) {
                return nil
            }
        }
    }
}

func writeAndCheck(port serial.Port, cmd string, successStr []byte, timeout time.Duration) error {
    if _, err := port.Write([]byte(cmd)); err != nil {
        return fmt.Errorf("write failed: %w", err)
    }
    // The Python code does read_until(...), so reuse readUntil logic:
    if err := readUntil(port, successStr, timeout); err != nil {
        return fmt.Errorf("did not receive success string '%s': %w", successStr, err)
    }
    return nil
}

func (b *BotaSensor) Start() {
    b.waitGroup.Add(1)
    go b.processData()
}

func (b *BotaSensor) processData() {
    defer b.waitGroup.Done()

    table := crc16.MakeTable(crc16.CRC16_X_25)
    frameSynced := false

    for {
        select {
        case <-b.stopCh:
            return

        default:
        }

        if !frameSynced {
            // Try to find the header
            headerByte := make([]byte, 1)
            _, err := b.port.Read(headerByte)
            if err != nil {
                // Possibly a timeout, or the port got closed.
                // You might handle errors differently or sleep briefly
                continue
            }

            if headerByte[0] == b.header {
                // Read 34 data bytes
                dataFrame := make([]byte, 34)
                n, err := b.port.Read(dataFrame)
                if err != nil || n < 34 {
                    continue
                }

                // Then read 2 bytes of CRC
                crcBytes := make([]byte, 2)
                n, err = b.port.Read(crcBytes)
                if err != nil || n < 2 {
                    continue
                }

                // Convert the 2 CRC bytes into a uint16 (little-endian)
                crcFrame := binary.LittleEndian.Uint16(crcBytes)

                // Calculate our own checksum
                csum := crc16.Checksum(dataFrame, table)

                if csum == crcFrame {
                    frameSynced = true
                } else {
                    // In Python, we do self._ser.read(1) to shift one byte
                    // We can mimic that here
                    b.port.Read(make([]byte, 1))
                }
            }
            continue
        }

        // If frameSynced
        headerByte := make([]byte, 1)
        _, err := b.port.Read(headerByte)
        if err != nil {
            // Possibly a timeout or closed port
            frameSynced = false
            continue
        }

        // Check if we lost the header
        if headerByte[0] != b.header {
            frameSynced = false
            continue
        }

        // Read 34 data bytes
        dataFrame := make([]byte, 34)
        n, err := b.port.Read(dataFrame)
        if err != nil || n < 34 {
            frameSynced = false
            continue
        }

        // Then read 2 bytes of CRC
        crcBytes := make([]byte, 2)
        n, err = b.port.Read(crcBytes)
        if err != nil || n < 2 {
            frameSynced = false
            continue
        }

        crcFrame := binary.LittleEndian.Uint16(crcBytes)
        csum := crc16.Checksum(dataFrame, table)
        if csum != crcFrame {
            frameSynced = false
            continue
        }

        // Parse dataFrame
        buf := bytes.NewReader(dataFrame)

        // Read status (2 bytes, little-endian)
        var status uint16
        if err := binary.Read(buf, binary.LittleEndian, &status); err != nil {
            frameSynced = false
            continue
        }

        // Read fx, fy, fz, mx, my, mz (float32 each)
        var fx, fy, fz, mx, my, mz float32
        if err := binary.Read(buf, binary.LittleEndian, &fx); err != nil {
            frameSynced = false
            continue
        }
        if err := binary.Read(buf, binary.LittleEndian, &fy); err != nil {
            frameSynced = false
            continue
        }
        if err := binary.Read(buf, binary.LittleEndian, &fz); err != nil {
            frameSynced = false
            continue
        }
        if err := binary.Read(buf, binary.LittleEndian, &mx); err != nil {
            frameSynced = false
            continue
        }
        if err := binary.Read(buf, binary.LittleEndian, &my); err != nil {
            frameSynced = false
            continue
        }
        if err := binary.Read(buf, binary.LittleEndian, &mz); err != nil {
            frameSynced = false
            continue
        }

        // Read timestamp (uint32) and convert to float32 in seconds
        var timestampRaw uint32
        if err := binary.Read(buf, binary.LittleEndian, &timestampRaw); err != nil {
            frameSynced = false
            continue
        }
        timestamp := float32(timestampRaw) * 1e-6

        // Read temperature (float32)
        var temperature float32
        if err := binary.Read(buf, binary.LittleEndian, &temperature); err != nil {
            frameSynced = false
            continue
        }

        // Update sensor data
        b.mux.Lock()
        b.status = status
        b.reading = BotaReading{
            Fx:          fx,
            Fy:          fy,
            Fz:          fz,
            Mx:          mx,
            My:          my,
            Mz:          mz,
            Timestamp:   timestamp,
            Temperature: temperature,
        }
        b.mux.Unlock()
    }
}

func (b *BotaSensor) Read() []float64 {
    b.mux.RLock()
    defer b.mux.RUnlock()

    
    force := [3]float64{
        float64(b.reading.Fx),
        float64(b.reading.Fy),
        float64(b.reading.Fz),
    }

    torque := [3]float64{
        float64(b.reading.Mx),
        float64(b.reading.My),
        float64(b.reading.Mz),
    }

    force = rotateZ(force, -45)
    torque = rotateZ(torque, -45)

    // d := 0.135
    // torque = FingertipTorque(torque, force, d)
    
    return []float64{
        force[0],
        force[1],
        force[2],
        torque[0],
        torque[1],
        torque[2],
    }
}

func (b *BotaSensor) Close() {
    close(b.stopCh)
    b.waitGroup.Wait()
    b.port.Close()
}

func FingertipTorque(torque, force [3]float64, d float64) [3]float64 {
	// Compute the additional torque component from the force due to the displacement:
	// r x F = [ -d*Fy, d*Fx, 0 ]
	return [3]float64{
		torque[0] - d*force[1],
		torque[1] + d*force[0],
		torque[2], // Tz remains unchanged.
	}
}

func rotateZ(v [3]float64, theta float64) [3]float64 {
	// Convert theta from degrees to radians.
	rad := theta * math.Pi / 180.0
	cosTheta := math.Cos(rad)
	sinTheta := math.Sin(rad)
	
	// Rotate the x and y components.
	xRot := v[0]*cosTheta - v[1]*sinTheta
	yRot := v[0]*sinTheta + v[1]*cosTheta
	
	return [3]float64{xRot, yRot, v[2]}
}
