#!/usr/bin/env python3
"""Server for multithreaded (asynchronous) chat application."""
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import json
import random


# ###########<GAME LOGIC>################# #

# ##CONSTANTS## #
# @ used as separator-prefix (in case buffer fills up with more than 1 message)
# to contain both client and server in their entirety in 1 script each,
# there's a copy of these constants in both files (not elegant, but hey)
MESSAGE_SEPARATOR = "@"
PRIVATE_MSG_PREFIX = 'PRIVATE: '
PUBLIC_MSG_PREFIX = 'PUBLIC: '
PLAYER_LIST_MSG_PREFIX = 'PLAYER_LIST: '
SET_NAME = "SET_NAME"
SET_PLAYER = "SET_PLAYER"
SET_SPECTATOR = "SET_SPECTATOR"
QUIT = "QUIT"


# ############# #
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
        self.broadcast_player_list()

    def broadcast_player_list(self):
        output = "Am Zug: "
        for player in self.player_queue:
            output += f"{self.names[player]}\n"
        broadcast(prefix=PLAYER_LIST_MSG_PREFIX, msg=output)
        print(f"broadcasting player list update: \n {output}")
        if self.player_queue:
            self.player_queue[0].send(bytes(f"{MESSAGE_SEPARATOR}{PRIVATE_MSG_PREFIX}Du bist dran!", "utf8"))

    def update(self, client, message: dict):
        """
        updates GameState, processing input from any of the clients;
        if necessary, triggers relevant broadcasts/sends
        :param message: input json dictionary as sent from one of the clients
        :param client: client of the game server connection
        :return:
        """
        print(f"Updating GameState with message'{message}'")
        if "PASS_DICE" in message:
            if self.player_queue[0] == client:
                self.end_turn()
                self.player_queue[-1].send(
                    bytes(f"{MESSAGE_SEPARATOR}{PRIVATE_MSG_PREFIX}Du hast die Würfel an {self.names[self.player_queue[0]]} weitergegeben!",
                          "utf8"))
        elif "REVEAL_DICE" in message:
            if self.player_queue[0] == client:
                broadcast(f"{self.names[client]} deckt auf: ({self.dies[0]}/{self.dies[1]})")
                self.player_queue[0].send(
                    bytes(f"{MESSAGE_SEPARATOR}{PRIVATE_MSG_PREFIX}Du hast die Würfel von {self.names[self.player_queue[-1]]} aufgedeckt!",
                          "utf8"))
                self.end_turn()
        elif "ROLL_DICE" in message:
            if self.player_queue[0] == client:
                self.dies = (random.randint(1, 6), random.randint(1, 6))
                self.player_queue[0].send(bytes(f"{MESSAGE_SEPARATOR}{PRIVATE_MSG_PREFIX}Deine Würfel: ({self.dies[0]}/{self.dies[1]})", "utf8"))
                self.end_turn()
        elif "SET_PLAYER" in message:
            if client in self.spectators:
                self.spectators.remove(client)
            if client not in self.player_queue:
                self.player_queue.append(client)
            client.send(bytes(f"{MESSAGE_SEPARATOR}{SET_PLAYER}", "utf8"))
            self.broadcast_player_list()
        elif "SET_SPECTATOR" in message:
            if client in self.player_queue:  # and self.player_queue[0] != client (do your turn first yo)
                self.player_queue.remove(client)
            if client not in self.spectators:
                self.spectators.append(client)
            client.send(bytes(f"{MESSAGE_SEPARATOR}{SET_SPECTATOR}", "utf8"))
            self.broadcast_player_list()
        else:
            print(f"Unexpected message: {message}. Aborting.")
            raise NotImplementedError


gameState = GameState()  # because global variables are fun


# ###########</GAME LOGIC>################ #


def accept_incoming_connections():
    """Sets up handling for incoming clients."""

    while True:
        client, client_address = SERVER.accept()
        print("%s:%s has connected." % client_address)
        client.send(bytes(f"{MESSAGE_SEPARATOR}{PRIVATE_MSG_PREFIX}Heeeey Lust auf Mäxxchen? \n ..bitte Name eingeben =)", "utf8"))
        addresses[client] = client_address
        clients.append(client)
        Thread(target=handle_client, args=(client,)).start()


def handle_client(client):  # Takes client socket as argument.
    """Handles a single client connection."""
    rcvd = client.recv(BUFSIZ).decode("utf8")
    first_contact = json.loads(rcvd)
    name = first_contact[SET_NAME]
    welcome = f'{MESSAGE_SEPARATOR}{PRIVATE_MSG_PREFIX}Hey %s! Alle Nachrichten in diesem Feld sind nur für deine Augen bestimmt!.' % name
    gameState.names[client] = name
    client.send(bytes(welcome, "utf8"))
    gameState.broadcast_player_list()

    while True:
        msg = client.recv(BUFSIZ)
        msg = msg.decode("utf-8")  # convert from bytes to string
        print(f"handling message from client {gameState.names[client]}: \n {msg}")
        json_dict = json.loads(msg)
        if QUIT not in json_dict:
            gameState.update(client=client, message=json_dict)
        else:
            #TODO: clean up this block and handle quitting a little more explicitely
            print(f"client{client} sent unexpected message: {msg}; closing connection")
            client.send(bytes(f"{MESSAGE_SEPARATOR}{QUIT}", "utf8"))
            client.close()
            clients.remove(client)
            if client in gameState.player_queue:
                gameState.player_queue.remove(client)
            if client in gameState.spectators:
                gameState.spectators.remove(client)
            del gameState.names[client]
            del addresses[client]
            gameState.broadcast_player_list()
            break


def broadcast(msg, prefix=PUBLIC_MSG_PREFIX):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""
    # TODO: have byte encoding and decoding happen in exactly 1 place respectively
    for sock in clients:
        sock.send(bytes(f"{MESSAGE_SEPARATOR}{prefix+msg}", "utf8"))





clients = []
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
