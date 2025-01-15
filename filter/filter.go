package filter

import (
    "reflect"
    "github.com/vistormu/goraspio/algos"
)

type FieldFilter struct {
    Median *algos.MedianFilter
    Kalman *algos.KalmanFilter
}

type ReadingFilter[T any] struct {
    filters map[string]*FieldFilter
}

func NewFilter[T any](medianWindowSize int, processVar, measVar, initErrCovar float64, initEst T) ReadingFilter[T] {
    filters := make(map[string]*FieldFilter)

    v := reflect.ValueOf(initEst)
    typeOfS := v.Type()

    for i := 0; i < v.NumField(); i++ {
        fieldName := typeOfS.Field(i).Name
        fieldValue := v.Field(i).Interface().(float32)

        filters[fieldName] = &FieldFilter{
            Median: algos.NewMedianFilter(medianWindowSize),
            Kalman: algos.NewKalmanFilter(processVar, measVar, initErrCovar, float64(fieldValue)),
        }
    }

    return ReadingFilter[T]{filters: filters}
}

func (rf *ReadingFilter[T]) Compute(reading T) T {
    v := reflect.ValueOf(reading)
    typeOfS := v.Type()

    result := reflect.New(typeOfS).Elem() // Create a new instance of T

    for i := 0; i < v.NumField(); i++ {
        fieldName := typeOfS.Field(i).Name
        if filter, exists := rf.filters[fieldName]; exists {
            fieldValue := v.Field(i).Interface().(float32)
            filteredValue := filter.Kalman.Compute(
                float64(filter.Median.Compute(float64(fieldValue))),
            )
            result.Field(i).SetFloat(float64(filteredValue))
        } else {
            // Copy the value directly if it's not a float32 field
            result.Field(i).Set(v.Field(i))
        }
    }

    return result.Interface().(T)
}
