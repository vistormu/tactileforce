package sensors

import (
    "github.com/vistormu/go-berry/comms"
	"github.com/vistormu/go-berry/peripherals"
)


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
