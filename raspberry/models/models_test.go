package models

import (
	"fmt"
	"testing"

	"github.com/vistormu/go-berry/ml"
)

func TestMain(t *testing.T) {
    model, err := ml.NewLocalModel(
        "transformer.onnx",
        4,
        3,
    )
    if err != nil {
        t.Fatal(err)
    }

    output, err := model.Compute([]float64{0.0, 0.0, 0.0, 0.0})
    if err != nil {
        t.Fatal(err)
    }

    fmt.Println(output)
}
