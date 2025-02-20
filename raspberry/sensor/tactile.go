package sensor

import (
    "github.com/vistormu/go-berry/comms"
	"github.com/vistormu/go-berry/peripherals"
	"github.com/vistormu/go-berry/utils/signal"
)

// ======
// FILTER
// ======
type TactileFilter struct {
    // median filter
    window int
    postWindow int
    median *signal.MultiMedianFilter[float64]
    postMedian *signal.MultiMedianFilter[float64]

    // kalman filter
    pVar float64
    mVar float64
    eCovar float64
    kalman *signal.MultiKalmanFilter[float64]
    
    threshold float64
    readingInit []float64
}

func NewTactileFilter(window, postWindow int, threshold float64, pVar, mVar, eCovar float64, readingInit []float64) *TactileFilter {
    return &TactileFilter{
        window: window,
        postWindow: postWindow,
        median: signal.NewMultiMedianFilter[float64](window, len(readingInit)),
        postMedian: signal.NewMultiMedianFilter[float64](postWindow, len(readingInit)),
        pVar: pVar,
        mVar: mVar,
        eCovar: eCovar,
        kalman: signal.NewMultiKalmanFilter(pVar, mVar, eCovar, readingInit),
        threshold: threshold,
        readingInit: readingInit,
    }
}

func (f *TactileFilter) Compute(reading []float64) []float64 {
    reading = f.median.Compute(reading)
    reading = f.kalman.Compute(reading)
    
    readingRel := make([]float64, 4)
    for i, r := range reading {
        readingRel[i] = r - f.readingInit[i]
        if f.readingInit[i] != 0 {
            readingRel[i] /= f.readingInit[i]
        }
    }

    // below := true
    // for _, r := range reading {
    //     below = below && (r < f.threshold)
    // }
    // below = false

    // if below {
    //     reading = make([]float64, 4)
    //     f.postMedian = signal.NewMultiMedianFilter[float64](f.postWindow, len(f.readingInit))

    //     return reading
    // }

    return f.postMedian.Compute(readingRel)
}

func (f *TactileFilter) Reset(readingInit []float64) {
    f.median = signal.NewMultiMedianFilter[float64](f.window, len(readingInit))
    f.postMedian = signal.NewMultiMedianFilter[float64](f.postWindow, len(readingInit))
    f.kalman = signal.NewMultiKalmanFilter(f.pVar, f.mVar, f.eCovar, readingInit)
    f.readingInit = readingInit
}

// ==============
// TACTILE SENSOR
// ==============
type TactileSensor struct {
    adc *peripherals.Mcp3204
    led *comms.DigitalOut
    vRef float64
}

func NewTactileSensor(vRef float64, chipSelectPinNo, onOffPinNo int) (*TactileSensor, error) {
    adc, err := peripherals.NewMcp3204(vRef, chipSelectPinNo)
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
        vRef: vRef,
    }, nil
}

func (s *TactileSensor) Read() ([]float64, error) {
    values := []float64{0, 0, 0, 0}
    for i := range values {
        value, err := s.adc.Read(i)
        if err != nil {
            return nil, err
        }

        values[i] = value / s.vRef
    }

    return values, nil
} 

func (s *TactileSensor) Close() error {
    s.adc.Close()
    s.led.Close()

    return nil
}
