package main

import (
	"github.com/62726164/bloom"
	"github.com/gorilla/mux"
	"github.com/gorilla/handlers"
	"math"
	"net/http"
	"os"
	"strings"
	"time"
	"encoding/json"
	"fmt"
	"log"
)

var fp = .000001
var n = 555278657.0
var m = math.Ceil((n * math.Log(fp)) / math.Log(1.0/math.Pow(2.0, math.Log(2.0))))
var k = uint(10)
var filter = bloom.New(uint(m), k)

var hex = "0123456789ABCDEF"

func hexOnly(hash string) bool {
	for _, c := range hash {
		if !strings.Contains(hex, string(c)) {
			return false
		}
	}
	return true
}

type Password struct {
  Hash string `json:"hash"`
}

type Response struct {
  PasswordLeaked bool `json:"passwordLeaked"`
}

func check(w http.ResponseWriter, r *http.Request) {
  var password Password
  err := json.NewDecoder(r.Body).Decode(&password)
  if err != nil {
      http.Error(w, err.Error(), http.StatusBadRequest)
      return
  }
	hash := strings.ToUpper(password.Hash)

	if len(hash) != 40 || !hexOnly(hash) {
		http.Error(w, http.StatusText(http.StatusBadRequest), http.StatusBadRequest)
	} else {
	  w.Header().Set("Content-Type", "application/json")
	  response := Response{}
	  if filter.Test([]byte(hash)) {
	    response.PasswordLeaked = true
	  } else {
	    response.PasswordLeaked = false
	  }
	  responseJson, _ := json.Marshal(response)
    fmt.Println(string(responseJson))
	  json.NewEncoder(w).Encode(&response)
	}
}

func main() {
	f, err := os.Open("./output.filter")
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	bytesRead, err := filter.ReadFrom(f)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("bytes read from filter: ", bytesRead)

	router := mux.NewRouter()
	router.HandleFunc("/password/sha1", check).Methods("POST")

	handler := handlers.CombinedLoggingHandler(os.Stdout, handlers.ProxyHeaders(router))
	server := &http.Server{
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		Addr:         "0.0.0.0:8080",
		Handler:      handler,
	}
	log.Fatal(server.ListenAndServe())
}
