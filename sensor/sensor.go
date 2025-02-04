package sensor

type Filter interface {
    Compute(value float64) float64
}

type FieldFilters struct {
    Kalman Filter
    Median Filter
}

