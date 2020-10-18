#!/usr/bin/env python3
"""Server for multithreaded (asynchronous) chat application."""
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import random
from typing import List

############<GAME LOGIC>##################

###CONSTANTS###
GAMESTATE_UPDATE_PREFIX = 'GAMESTATE_UPDATE_MSG: '


###############
class GameState:
    def __init__(self):
        self.player_queue = []  # active players
        self.spectators = []  # inactive players
        self.dies = (0, 0)  # (0, 0) indicating initial state
        self.names = {}


    def end_turn(self):
        """
        move top of the queue to the bottom
        :return:
        """
        self.player_queue = self.player_queue[1:]+[self.player_queue[0]]
        self.player_queue[0].send(bytes("it's your turn!", "utf8"))

    def update(self, client, message: str):
        """
        updates GameState, processing input from any of the clients;
        if necessary, triggers relevant broadcasts/sends
        :param message: input string as sent from one of the clients;
            GAMESTATE_UPDATE_PREFIX has already been removed at this stage,
            leaving us with (example):


                PASS_DICE
                REVEAL_DICE
                ROLL_DICE
                SET_NAMEawesomeName123
                SET_PLAYER
                SET_SPECTATOR


        :param client: client of the game server connection
        :return:
        """
        print(f"Updating GameState with message'{message}'")
        if message.startswith("PASS_DICE"):
            self.end_turn()
        elif message.startswith("REVEAL_DICE"):
            if self.player_queue[0] == client:
                broadcast(f"{self.names[client]} reveals the dies: {self.dies}")
                self.end_turn()
        elif message.startswith("ROLL_DICE"):
            if self.player_queue[0] == client:
                self.dies = (random.randint(1, 6), random.randint(1, 6))
                self.player_queue[0].send(bytes(f"you've rolled {self.dies}", "utf8"))
                self.end_turn()
        elif message.startswith("SET_NAME"):
            self.names[client] = message.remove("SET_NAME")
        elif message.startswith("SET_PLAYER"):
            if client in self.spectators:
                self.spectators.remove(client)
                self.player_queue.append(client)
        elif message.startswith("SET_SPECTATOR"):
            if client in self.player_queue:  # and self.player_queue[0] != client (do your turn first yo)
                self.player_queue.remove(client)
                self.spectators.append(client)
        else:
            print(f"Unexpected message: {message}. Aborting.")
            raise NotImplementedError

    def __repr__(self):
        """
        string representation of the GameState, to be used for 'public' broadcasts

        :return:
        """


gameState = GameState()  # because global variables are fun


############</GAME LOGIC>#################


def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s has connected." % client_address)
        client.send(bytes("Greetings from the cave! Now type your name and press enter!", "utf8"))
        addresses[client] = client_address
        gameState.player_queue.append(client)
        Thread(target=handle_client, args=(client,)).start()


def handle_client(client):  # Takes client socket as argument.
    """Handles a single client connection."""

    name = client.recv(BUFSIZ).decode("utf8")
    welcome = 'Welcome %s! If you ever want to quit, type {quit} to exit.' % name
    gameState.names[client] = name
    client.send(bytes(welcome, "utf8"))
    msg = "%s has joined the chat!" % name
    broadcast(bytes(msg, "utf8"))
    clients[client] = name  # store name to the GameState

    while True:
        msg = client.recv(BUFSIZ)
        msg = msg.decode("utf-8")  # convert from bytes to string
        print(f"handling message: \n {msg}")
        if msg.startswith(f"{GAMESTATE_UPDATE_PREFIX}"):
            print("message started with gamestate update prefix!")
            gameState.update(client=client, message=str(msg).replace(GAMESTATE_UPDATE_PREFIX, ""))
        elif msg != bytes("{quit}", "utf8"):
            broadcast(msg, name + ": ")
        else:
            client.send(bytes("{quit}", "utf8"))
            client.close()
            del clients[client]
            broadcast(bytes("%s has left the chat." % name, "utf8"))
            break


def broadcast(msg, prefix=""):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""

    for sock in clients:
        sock.send(bytes(prefix+msg, "utf8"))


clients = {}
addresses = {}

HOST = ''
PORT = 63001
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)



if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connection...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()