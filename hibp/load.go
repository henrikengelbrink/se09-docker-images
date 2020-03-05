package main

import (
	"bufio"
	"github.com/62726164/bloom"
	"log"
	"math"
	"os"
)

var fp = .000001
var n = 555278657.0
var m = math.Ceil((n * math.Log(fp)) / math.Log(1.0/math.Pow(2.0, math.Log(2.0))))
var k = uint(10)
var filter = bloom.New(uint(m), k)

func main() {
	hashFile := os.Args[1]
	filterFile := os.Args[2]

	file, err := os.Open(hashFile)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	for scanner.Scan() {
		filter.Add(scanner.Bytes())
	}

	err = scanner.Err()
	if err != nil {
		log.Fatal(err)
	}

	f, err := os.Create(filterFile)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	bytesWritten, err := filter.WriteTo(f)
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("Created bloom filter: %d\n", bytesWritten)
}