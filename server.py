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
DICE_MSG_PREFIX = "DICE: "
PRIVATE_MSG_PREFIX = 'PRIVATE: '
PUBLIC_MSG_PREFIX = 'PUBLIC: '
PLAYER_LIST_MSG_PREFIX = 'PLAYER_LIST: '

SET_NAME = "SET_NAME"
SET_PLAYER = "SET_PLAYER"
SET_SPECTATOR = "SET_SPECTATOR"
QUIT = "QUIT"

MÄXCHEN = (2, 1)
REWARD = 'Punkt'

# ############# #
class GameState:
    def __init__(self):
        self.player_queue = []  # active players
        self.spectators = []  # inactive players
        self.alea_iacta_est = False
        self.dice = (0, 0)  # (0, 0) indicating initial state
        self.names = {}
        self.points = {}
        self.last_declaration_tuple = (None, None)  # (Client, Dice Declaration Tuple)

    def end_turn(self):
        """
        move top of the queue to the bottom
        :return:
        """
        self.player_queue = self.player_queue[1:]+[self.player_queue[0]]
        self.alea_iacta_est = False
        self.broadcast_player_list()

    def broadcast_player_list(self):
        output = "Am Zug: "
        for player in self.player_queue:
            output += f"{self.names[player]}[{self.points[player]}]\n"
        if self.last_declaration_tuple[0]:
            output += f"Letzte Ansage von {self.names[self.last_declaration_tuple[0]]}: ({self.last_declaration_tuple[1][0]}/{self.last_declaration_tuple[1][1]})"
        broadcast(prefix=PLAYER_LIST_MSG_PREFIX, msg=output)
        print(f"broadcasting player list update: \n {output}")
        if self.player_queue:
            send(self.player_queue[0], {PRIVATE_MSG_PREFIX: "Du bist dran!"})

    @staticmethod
    def is_result_better(dice1, dice2):
        """
        compares dice1 and dice2 and determines if dice 1 is better than dice2
        """

        def is_pasch(dice):
            if dice[0] == dice[1]:
                return True
            else:
                return False

        result = None
        if dice1 == dice2:
            result = True
        elif dice1 == MÄXCHEN:
            result = True
        elif dice2 == MÄXCHEN:
            result = False
        elif is_pasch(dice1) and not is_pasch(dice2):
            result = True
        elif is_pasch(dice2) and not is_pasch(dice1):
            result = False
        elif dice1[0]*10+dice1[1] > dice2[0]*10+dice2[1]:
            result = True
        else:
            result = False
        return result

    def update(self, client, message: dict):
        """
        updates GameState, processing input from any of the clients;
        if necessary, triggers relevant broadcasts/sends
        :param message: input json dictionary as sent from one of the clients
        :param client: client of the game server connection
        :return:
        """
        print(f"Updating GameState with message'{message}'")
        for key in message:
            if "PASS_DICE" == key:
                if self.player_queue[0] == client:
                    self.end_turn()
                    send(self.player_queue[-1], {PRIVATE_MSG_PREFIX: f"Du hast die Würfel an {self.names[self.player_queue[0]]} weitergegeben!"})
            elif "REVEAL_DICE" == key:
                if self.player_queue[0] == client:
                    # let's find out who wins first:
                    claimed_dice = self.last_declaration_tuple[1]
                    actual_dice = self.dice
                    current_player = client
                    last_player = self.last_declaration_tuple[0]
                    winner = current_player if GameState.is_result_better(claimed_dice, actual_dice) else last_player
                    loser = current_player if current_player != winner else last_player
                    broadcast(f"{self.names[client]} deckt auf: ({self.dice[0]}/{self.dice[1]});\n"
                              f"{self.names[winner]} hat gewonnen, {self.names[loser]} bekommt als Trost einen Punkt!")
                    self.points[loser] += 1
                    send(self.player_queue[0], {PRIVATE_MSG_PREFIX: f"Du hast die Würfel von {self.names[self.player_queue[-1]]} aufgedeckt!"})
                    # manually move loser to front of queue and let them know it's their turn: #hacks
                    self.player_queue.remove(loser)
                    self.player_queue.insert(0, loser)
                    send(loser, {PRIVATE_MSG_PREFIX: f"Versuch's direkt noch mal, viel Glück beim nächsten Versuch!\n"
                                                     f"(du bist dran)"})
                    self.dice = (1, 0)  # reset dice
                    self.broadcast_player_list()

            elif "ROLL_DICE" == key:
                if self.player_queue[0] == client and not self.alea_iacta_est:
                    self.dice = (random.randint(1, 6), random.randint(1, 6))
                    self.alea_iacta_est = True
                    # presort dice by size:
                    if self.dice[1] > self.dice[0]:
                        self.dice = (self.dice[1], self.dice[0])
                    send(self.player_queue[0], {DICE_MSG_PREFIX: f"Deine Würfel: ({self.dice[0]}/{self.dice[1]}). \n"
                                                                 f"Welches Würfelergebnis willst du offiziell angeben?"})
                    # inform last player that they're safe now:
                    if self.last_declaration_tuple[0] and self.last_declaration_tuple[0] != client:
                        send(self.last_declaration_tuple[0], {PRIVATE_MSG_PREFIX: f"{self.names[self.player_queue[0]]} hat weitergewürfelt.\nGut gespielt! :D"})
            elif "SET_PLAYER" == key:
                if client in self.spectators:
                    self.spectators.remove(client)
                if client not in self.player_queue:
                    self.player_queue.append(client)
                send(client, {SET_PLAYER: True})
                self.broadcast_player_list()
            elif "SET_SPECTATOR" == key:
                if client in self.player_queue:  # and self.player_queue[0] != client (do your turn first yo)
                    self.player_queue.remove(client)
                if client not in self.spectators:
                    self.spectators.append(client)
                send(client, {SET_SPECTATOR: True})
                self.broadcast_player_list()
            elif DICE_MSG_PREFIX == key:
                if self.player_queue[0] == client:
                    self.last_declaration_tuple = (client, message[key])
                    declaration_msg = f"Du hast ({self.dice[0]}/{self.dice[1]}) gewürfelt und ({message[key][0]}/{message[key][1]}) angegeben.\n"
                    if GameState.is_result_better(message[key], self.dice):
                        declaration_msg += "Du Schlingel! :D"
                    else:
                        declaration_msg += "Alles in bester Ordnung."
                    send(client, {PRIVATE_MSG_PREFIX: declaration_msg})
                    self.end_turn()
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
        send(client, {PRIVATE_MSG_PREFIX: "Heeeey Lust auf Mäxxchen? \n ..bitte Name eingeben =)"})
        addresses[client] = client_address
        clients.append(client)
        Thread(target=handle_client, args=(client,)).start()


def handle_client(client):  # Takes client socket as argument.
    """Handles a single client connection."""
    rcvd = client.recv(BUFSIZ).decode("utf8")
    first_contact = json.loads(rcvd)
    name = first_contact[SET_NAME]
    welcome = f'Hey %s! Alle Nachrichten in diesem Feld sind nur für deine Augen bestimmt!.' % name
    gameState.names[client] = name
    gameState.points[client] = 0
    send(client, {PRIVATE_MSG_PREFIX: welcome})
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
            send(client, {QUIT: True})
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


def broadcast(msg: str, prefix=PUBLIC_MSG_PREFIX):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""
    # TODO: broadcast and send accepting str/dict respectively feels wrong, might need streamlining
    for sock in clients:
        send(sock, {prefix: msg})


def send(client, msg: dict):
    client.send(bytes(MESSAGE_SEPARATOR+json.dumps(msg), "utf8"))




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
