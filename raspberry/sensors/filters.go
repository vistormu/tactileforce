package sensors

import (
	"github.com/vistormu/go-berry/utils/signal"
	"github.com/vistormu/go-berry/utils/num"
)


type Filter[T num.Number] struct {
    // median filter
    window int
    postWindow int
    median *signal.MultiMedianFilter[T]
    postMedian *signal.MultiMedianFilter[T]

    // kalman filter
    pVar float64
    mVar float64
    eCovar float64
    kalman *signal.MultiKalmanFilter[T]

    // stages
    relativeFiltering bool
    thresholdFiltering bool
    postMedianFiltering bool
    
    threshold T
    readingInit []T
}

func NewFilter[T num.Number](window, postWindow int, threshold T, pVar, mVar, eCovar float64, readingInit []T, relativeFiltering, thresholdFiltering, postMedianFiltering bool) *Filter[T] {
    return &Filter[T]{
        window: window,
        postWindow: postWindow,
        median: signal.NewMultiMedianFilter[T](window, len(readingInit)),
        postMedian: signal.NewMultiMedianFilter[T](postWindow, len(readingInit)),
        pVar: pVar,
        mVar: mVar,
        eCovar: eCovar,
        kalman: signal.NewMultiKalmanFilter(pVar, mVar, eCovar, readingInit),
        threshold: threshold,
        readingInit: readingInit,
        relativeFiltering: relativeFiltering,
        thresholdFiltering: thresholdFiltering,
        postMedianFiltering: postMedianFiltering,
    }
}

func (f *Filter[T]) Compute(reading []T) []T {
    // median filter
    reading = f.median.Compute(reading)

    // kalman filter
    reading = f.kalman.Compute(reading)
    
    // relative filtering
    for i := range reading {
        reading[i] = reading[i] - f.readingInit[i]
        if f.readingInit[i] != 0 && f.relativeFiltering {
            reading[i] /= f.readingInit[i]
        }
    }

    // threshold filtering
    if f.thresholdFiltering {
        below := true
        for _, r := range reading {
            below = below && (r < f.threshold)
        }
        below = false

        if below {
            reading = make([]T, len(reading))
            f.Reset(reading)
        }
    }

    // post median filtering
    if f.postMedianFiltering {
        reading = f.postMedian.Compute(reading)
    }

    return reading
}

func (f *Filter[T]) Reset(readingInit []T) {
    f.median = signal.NewMultiMedianFilter[T](f.window, len(readingInit))
    f.postMedian = signal.NewMultiMedianFilter[T](f.postWindow, len(readingInit))
    f.kalman = signal.NewMultiKalmanFilter(f.pVar, f.mVar, f.eCovar, readingInit)
    f.readingInit = readingInit
}
