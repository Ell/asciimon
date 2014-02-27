// based on example found at https://github.com/tenntenn/golang-samples

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"

	"github.com/garyburd/redigo/redis"

	"code.google.com/p/go.net/websocket"
	"runtime"
)

// Chat server.
type Server struct {
	path         string
	clients      []*Client
	addClient    chan *Client
	removeClient chan *Client
	sendAll      chan string
	frame        string
}

// Create new chat server.
func NewServer(path string) *Server {
	clients := make([]*Client, 0)
	addClient := make(chan *Client)
	removeClient := make(chan *Client)
	sendAll := make(chan string)
	messages := ""
	return &Server{path, clients, addClient, removeClient, sendAll, messages}
}

func (self *Server) Listen() {
	log.Println("Starting websocket handler")

	// redis streaming
	go self.ReadFrames()

	// websocket handler
	onConnected := func(ws *websocket.Conn) {
		client := NewClient(ws, self)
		self.addClient <- client
		client.Listen()
	}
	http.Handle(self.path, websocket.Handler(onConnected))

	for {
		select {
		case c := <-self.addClient:
			self.clients = append(self.clients, c)
			c.send <- self.frame
			log.Println("Added new client:", len(self.clients), "total.")
		case c := <-self.removeClient:
			self.disconnectClient(c)
			log.Println("Removed a client:", len(self.clients), "total.", runtime.NumGoroutine(), " goroutines left.")
		case msg := <-self.sendAll:
			for i := 0; i < len(self.clients); i++ {
				c := self.clients[i]
				select {
				case c.send <- msg:
				default:
					self.disconnectClient(c)
					i--  // self.clients[i] was just deleted
					log.Println("Removed a slow client:", len(self.clients), "total.", runtime.NumGoroutine(), " goroutines left.")
				}
			}
		}
	}
}

func (self *Server) disconnectClient(c *Client) bool {
	for i := range self.clients {
		if self.clients[i] == c {
			close(c.done)
			c.conn.Close()
			self.clients[i], self.clients = self.clients[len(self.clients)-1], self.clients[:len(self.clients)-1]
			return true
		}
	}
	return false
}

type Frame struct {
	Delta    string `json:"dithered_delta"`
	Dithered string `json:"dithered"`
}

func (self *Server) ReadFrames() {
	c, err := redis.Dial("tcp", ":6379")
	if err != nil {
		panic(err)
	}

	psc := redis.PubSubConn{c}
	psc.Subscribe("pokemon")
	for {
		switch v := psc.Receive().(type) {
		case redis.Message:
			frame := &Frame{}
			err := json.Unmarshal(v.Data, &frame)
			if err != nil {
				continue
			}
			self.sendAll <- frame.Delta
			self.frame = "0\t" + frame.Dithered
		case redis.Subscription:
			fmt.Printf("%s: %s %d\n", v.Channel, v.Kind, v.Count)
		case error:
			panic(v)
		}
	}
}

// Chat client.
type Client struct {
	conn   *websocket.Conn
	server *Server
	send   chan string
	done   chan bool
}

const channelBufSize = 100

// Create new chat client.
func NewClient(ws *websocket.Conn, server *Server) *Client {
	send := make(chan string, channelBufSize)
	done := make(chan bool)
	return &Client{ws, server, send, done}
}

// Listen Write and Read request via chanel
func (self *Client) Listen() {
	go self.listenWrite()
	self.listenRead()
}

// Listen write request via chanel
func (self *Client) listenWrite() {
	for {
		select {
		case <-self.done:
			return
		case msg := <-self.send:
			err := websocket.Message.Send(self.conn, msg)
			if err != nil {
				self.server.removeClient <- self
				return
			}
		}
	}
}

// Listen read request via chanel
func (self *Client) listenRead() {
	for {
		select {
		case <-self.done:
			return
		default:
			var msg []byte
			err := websocket.Message.Receive(self.conn, &msg)
			if err != nil {
				self.server.removeClient <- self
				return
			}
		}
	}
}

var addr = flag.String("addr", "0.0.0.0:8000", "bind address & port")

func main() {
	flag.Parse()
	server := NewServer("/pokemon")
	go server.Listen()
	http.Handle("/", http.FileServer(http.Dir(".")))
	for _, path := range []string{"static"} {
		http.Handle("/"+path+"/", http.StripPrefix("/"+path+"/", http.FileServer(http.Dir(path))))
	}
	log.Fatal(http.ListenAndServe(*addr, nil))
}
