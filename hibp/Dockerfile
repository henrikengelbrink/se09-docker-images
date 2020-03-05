FROM golang as bloombuilder
RUN go get github.com/62726164/bloom
COPY ./load.go ./load.go
COPY ./pw_only.txt ./pw_only.txt
#COPY ./test.txt ./test.txt
RUN go build -o load load.go
RUN mkdir /output_volume
RUN ./load ./pw_only.txt ./output.filter
#RUN ./load ./test.txt ./output.filter

FROM golang as appbuilder
RUN go get github.com/62726164/bloom
RUN go get github.com/gorilla/handlers
RUN go get github.com/gorilla/mux
COPY ./main.go ./main.go
RUN go build -o app main.go

FROM ubuntu:18.04
RUN mkdir /app
WORKDIR /app
COPY --from=bloombuilder /go/output.filter /app
COPY --from=appbuilder /go/app /app
CMD ["/app/app"]
