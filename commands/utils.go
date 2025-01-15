package commands

import (
    "sort"
    "github.com/lithammer/fuzzysearch/fuzzy"
)


func findClosestMatch(input string, keys []string) string {
	matches := fuzzy.RankFind(input, keys)

	if len(matches) > 0 {
		sort.Sort(matches)
		return matches[0].Target
	}

	closest := ""
	minDistance := len(input) + 1
	for _, key := range keys {
		distance := fuzzy.LevenshteinDistance(input, key)
		if distance < minDistance {
			minDistance = distance
			closest = key
		}
	}

	if minDistance <= len(input)/2 {
		return closest
	}

	return ""
}

func keys[T any](m map[string]T) []string {
    keys := make([]string, 0, len(m))
    for k := range m {
        keys = append(keys, k)
    }
    return keys
}
