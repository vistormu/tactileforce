package configs

import (
    "github.com/BurntSushi/toml"
)

type Config struct {
	Simulation SimulationConfig `toml:"simulation"`
	Client     ClientConfig     `toml:"client"`
    BotaSensor BotaSensorConfig `toml:"bota_sensor"`
    TactileSensor TactileSensorConfig `toml:"tactile_sensor"`
	Model      ModelConfig      `toml:"model"`
}

type SimulationConfig struct {
	ExecutionTime   int     `toml:"execution_time"`
	Dt              float64 `toml:"dt"`
    CalibrationTime int     `toml:"calibration_time"`
    CalibrationTrim int     `toml:"calibration_trim"`
}

type ClientConfig struct {
	Ip   string `toml:"ip"`
	Port int    `toml:"port"`
}

type BotaSensorConfig struct {
    Port         string `toml:"port"`
    KalmanFilter KalmanFilterConfig `toml:"kf"`
    MedianFilter MedianFilterConfig `toml:"mf"`
}

type TactileSensorConfig struct {
    VRef float64 `toml:"v_ref"`
    ChipSelect int `toml:"chip_select"`
    LedOnOff int `toml:"led_on_off"`
    KalmanFilter KalmanFilterConfig `toml:"kf"`
    MedianFilter MedianFilterConfig `toml:"mf"`
}

type KalmanFilterConfig struct {
	ProcessVariance        float64 `toml:"process_variance"`
	MeasurementVariance    float64 `toml:"measurement_variance"`
	InitialErrorCovariance float64 `toml:"initial_error_covariance"`
}

type MedianFilterConfig struct {
	Window int `toml:"window"`
    PostWindow int `toml:"post_window"`
    Threshold float64 `toml:"threshold"`
}

type ModelConfig struct {
    Local bool `toml:"local"`
    Path string `toml:"path"`
    NInputs int `toml:"n_inputs"`
    NOutputs int `toml:"n_outputs"`
    MedianFilter MedianFilterConfig `toml:"mf"`
}

func LoadConfig() (*Config, error) {
    config := &Config{}
    _, err := toml.DecodeFile("configs/config.toml", config)

    return config, err
}
