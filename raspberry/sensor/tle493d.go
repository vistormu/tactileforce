package sensor

import (
	"fmt"

	"github.com/vistormu/go-berry/comms"
)

type Tle493e struct {
    i2c *comms.I2C
    offset int
    prevData int
    resetCount int
}

func NewTle493e(address byte, line int) (*Tle493e, error) {
    i2c, err := comms.NewI2C(address, line)
    if err != nil {
        return nil, err
    }

    s := &Tle493e{i2c, 0, 0, 0}

    s.offset, err = s.read()
    if err != nil {
        return nil, err
    }
    s.prevData = s.offset

    return s, nil
}

func (s *Tle493e) read() (int, error) {
    data, err := s.i2c.Read([]byte{0x00, 0x01, 0x02, 0x03, 0x04, 0x05}, []int{1, 1, 1, 1, 1, 1})
    if err != nil {
        return -1, err
    }

    fmt.Println(data)

    value := (uint16(data[0]) << 8) | (uint16(data[1]) & 0xF0)

    return int(value), nil
}

func (s *Tle493e) Read() (float64, error) {
    data, err := s.read()
    if err != nil {
        return -1, err
    }

    degreeValue := float64(data) / 4095 * 360
    
    return degreeValue, nil
}

func (s *Tle493e) Close() error {
    err := s.i2c.Close()
    if err != nil {
        return err
    }

    return nil
}

