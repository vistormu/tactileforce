package sensor

import (
	// "time"

	"github.com/vistormu/go-berry/comms"
	"github.com/vistormu/go-berry/utils/signal"
)

// ===
// ADC
// ===
type Mcp3204 struct {
    spi *comms.Spi
    vRef float64
}

func NewMcp3204(vRef float64, chipSelectPinNo int) (*Mcp3204, error) {
    spi, err := comms.NewSpi(chipSelectPinNo, 0, 0, 1.6e6) 
    if err != nil {
        return nil, err
    }
    
    return &Mcp3204{
        spi: spi,
        vRef: vRef,
    }, nil
}

func (m Mcp3204) Read(channel int) (float64, error) {
    cmd := make([]byte, 3)
    cmd[0] = 0x06 + (byte(channel) >> 2)
	cmd[1] = (byte(channel) & 0x03) << 6
	cmd[2] = 0x00

    data := make([]byte, 3)
    copy(data, cmd)
    m.spi.Exchange(data)

    value := ((int(data[1]) & 0x0F) << 8) | int(data[2])
    voltage := (float64(value) / 4095) * m.vRef

    return voltage, nil
}

func (m Mcp3204) Close() error {
    err := m.spi.Close()
    if err != nil {
        return err
    }

    return nil
}


// =======
// READING
// =======
type TactileReading struct {
    S0v float64
    S1v float64
    S2v float64
    S3v float64
    // S0b float64
    // S1b float64
    // S2b float64
    // S3b float64
}

func (tr1 TactileReading) Sub(tr2 TactileReading) TactileReading {
    return TactileReading{
       S0v: tr1.S0v - tr2.S0v,
       S1v: tr1.S1v - tr2.S1v,
       S2v: tr1.S2v - tr2.S2v,
       S3v: tr1.S3v - tr2.S3v,
       // S0b: tr1.S0b - tr2.S0b,
       // S1b: tr1.S1b - tr2.S1b,
       // S2b: tr1.S2b - tr2.S2b,
       // S3b: tr1.S3b - tr2.S3b,
    }
}

func TactileReadingMean(readings []TactileReading) TactileReading {
    var sum TactileReading
    count := len(readings)

    for _, r := range readings {
        sum.S0v += r.S0v
        sum.S1v += r.S1v
        sum.S2v += r.S2v
        sum.S3v += r.S3v
        // sum.S0b += r.S0b
        // sum.S1b += r.S1b
        // sum.S2b += r.S2b
        // sum.S3b += r.S3b
    }

    mean := TactileReading{
        S0v: sum.S0v / float64(count),
        S1v: sum.S1v / float64(count),
        S2v: sum.S2v / float64(count),
        S3v: sum.S3v / float64(count),
        // S0b: sum.S0b / float64(count),
        // S1b: sum.S1b / float64(count),
        // S2b: sum.S2b / float64(count),
        // S3b: sum.S3b / float64(count),
    }

    return mean
}

// ======
// FILTER
// ======
type TactileFilter struct {
    S0v FieldFilters
    S1v FieldFilters
    S2v FieldFilters
    S3v FieldFilters
    // S0b FieldFilters
    // S1b FieldFilters
    // S2b FieldFilters
    // S3b FieldFilters
}

func NewTactileFilter(window int, pVar, mVar, eCovar float64, initial TactileReading) *TactileFilter {
    return &TactileFilter{
        S0v: FieldFilters{
            Median: signal.NewMedianFilter(window),
            Kalman: signal.NewKalmanFilter(pVar, mVar, eCovar, initial.S0v),
        },
        S1v: FieldFilters{
            Median: signal.NewMedianFilter(window),
            Kalman: signal.NewKalmanFilter(pVar, mVar, eCovar, initial.S1v),
        },
        S2v: FieldFilters{
            Median: signal.NewMedianFilter(window),
            Kalman: signal.NewKalmanFilter(pVar, mVar, eCovar, initial.S2v),
        },
        S3v: FieldFilters{
            Median: signal.NewMedianFilter(window),
            Kalman: signal.NewKalmanFilter(pVar, mVar, eCovar, initial.S3v),
        },
        // S0b: FieldFilters{
        //     Median: signal.NewMedianFilter(window),
        //     Kalman: signal.NewKalmanFilter(pVar, mVar, eCovar, initial.S0b),
        // },
        // S1b: FieldFilters{
        //     Median: signal.NewMedianFilter(window),
        //     Kalman: signal.NewKalmanFilter(pVar, mVar, eCovar, initial.S1b),
        // },
        // S2b: FieldFilters{
        //     Median: signal.NewMedianFilter(window),
        //     Kalman: signal.NewKalmanFilter(pVar, mVar, eCovar, initial.S2b),
        // },
        // S3b: FieldFilters{
        //     Median: signal.NewMedianFilter(window),
        //     Kalman: signal.NewKalmanFilter(pVar, mVar, eCovar, initial.S3b),
        // },
    }
}

func (f *TactileFilter) Compute(reading TactileReading) TactileReading {
    return TactileReading{
        S0v: f.S0v.Kalman.Compute(f.S0v.Median.Compute(reading.S0v)),
        S1v: f.S1v.Kalman.Compute(f.S1v.Median.Compute(reading.S1v)),
        S2v: f.S2v.Kalman.Compute(f.S2v.Median.Compute(reading.S2v)),
        S3v: f.S3v.Kalman.Compute(f.S3v.Median.Compute(reading.S3v)),
        // S0b: f.S0b.Kalman.Compute(f.S0b.Median.Compute(reading.S0b)),
        // S1b: f.S1b.Kalman.Compute(f.S1b.Median.Compute(reading.S1b)),
        // S2b: f.S2b.Kalman.Compute(f.S2b.Median.Compute(reading.S2b)),
        // S3b: f.S3b.Kalman.Compute(f.S3b.Median.Compute(reading.S3b)),
    }
}

// ==============
// TACTILE SENSOR
// ==============
type TactileSensor struct {
    adc *Mcp3204
    led *comms.DigitalOut
}

func NewTactileSensor(vRef float64, chipSelectPinNo, onOffPinNo int) (*TactileSensor, error) {
    adc, err := NewMcp3204(vRef, chipSelectPinNo)
    if err != nil {
        return nil, err
    }

    led, err := comms.NewDigitalOut(onOffPinNo, comms.Low)
    if err != nil {
        return nil, err
    }
    led.Toggle()

    return &TactileSensor{
        adc: adc,
        led: led,
    }, nil
}

func (s *TactileSensor) Read() (TactileReading, error) {
    // values
    // s.led.Write(comms.High) 
    // time.Sleep(time.Microsecond*50)

    values := [4]float64{0, 0, 0, 0}
    for i := range values {
        value, err := s.adc.Read(i)
        if err != nil {
            return TactileReading{}, err
        }

        values[i] = value / s.adc.vRef
    }
    
    // biases
    // s.led.Write(comms.Low)
    // time.Sleep(time.Microsecond*50)

    // biases := [4]float64{0, 0, 0, 0}
    // for i := range biases {
    //     value, err := s.adc.Read(i)
    //     if err != nil {
    //         return TactileReading{}, err
    //     }

    //     biases[i] = value / s.adc.vRef
    // }

    return TactileReading{
        S0v: values[0],
        S1v: values[1],
        S2v: values[2],
        S3v: values[3],
        // S0b: biases[0],
        // S1b: biases[1],
        // S2b: biases[2],
        // S3b: biases[3],
    }, nil
} 

func (s *TactileSensor) Close() error {
    s.adc.Close()
    s.led.Close()

    return nil
}
