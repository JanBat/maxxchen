#!/usr/bin/env python3
"""Modified Script for Tkinter GUI chat client."""

from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter
import json


# ###########<GAME LOGIC>################# #
# @ used as separator-prefix (in case buffer fills up with more than 1 message) TODO: use jsons instead
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

# ###########</GAME LOGIC>################ #
BUFSIZ: int = 1024
DEFAULT_ADDRESS: str = "192.168.1.10"
DEFAULT_PORT: int = 63001


class Connection:
    """handles collection and storage of connection data (port+host). does not actually connect to anything"""
    PORT = ""
    HOST = ""

    @classmethod
    def setup(cls):
        """collect PORT and HOST information as user input in separate mini app"""

        connection_app = tkinter.Tk()
        connection_app.protocol("WM_DELETE_WINDOW", lambda: connection_app.destroy())
        msg_string: tkinter.StringVar = tkinter.StringVar()
        msg_string.set("Bitte Adresse eingeben!")
        msg = tkinter.Message(connection_app, textvariable=msg_string, relief=tkinter.RAISED, width=500)
        msg.pack(side=tkinter.TOP)

        entry_string: tkinter.StringVar = tkinter.StringVar()
        entry_string.set(DEFAULT_ADDRESS)
        entry_field = tkinter.Entry(connection_app, textvariable=entry_string)
        entry_field.pack(side=tkinter.TOP)

        def set_host(event=None):
            Connection.HOST = entry_string.get()
            entry_string.set(DEFAULT_PORT)
            entry_field.bind("<Return>", set_port)
            msg_string.set("Bitte Port eingeben!")

        def set_port(event=None):
            Connection.PORT = int(entry_string.get())
            connection_app.destroy()

        entry_field.bind("<Return>", set_host)


class App:

    class AppSection:
        def __init__(self, top, orientation=tkinter.LEFT, fill=tkinter.NONE):
            self.components = []
            self.frame: tkinter.Frame = tkinter.Frame(top)
            self.orientation = orientation
            self.fill = fill

        # functions for managing abstract visible components (buttons, text fields)

        def _add_component(self, component):
            self.components.append(component)
            component.pack(side=self.orientation, fill=self.fill)
            self.frame.pack()  # not sure if correct place for this (TODO: find out)

        def add_button(self, text: str, command):
            new_button: tkinter.Button = tkinter.Button(self.frame, text=text, command=command)
            self._add_component(new_button)
            return new_button

        def add_entry(self, textvariable: tkinter.StringVar):
            new_entry: tkinter.Entry = tkinter.Entry(self.frame, textvariable=textvariable)
            self._add_component(new_entry)
            return new_entry

        def add_message(self, textvariable: tkinter.StringVar, relief=tkinter.RAISED, width=500):
            msg = tkinter.Message(self.frame, textvariable=textvariable, relief=relief, width=width)
            self._add_component(msg)
            return msg

        def activate(self):
            for component in self.components:
                component.pack()  # there's possibly a more elegant way to do this

        def deactivate(self):
            for component in self.components:
                component.forget()  # grid_forget ?

    # App management:
    def connect(self):
        """create a connection to the server and start a thread to handle package reception"""
        if not Connection.HOST or not Connection.PORT:
            self.top.quit()

        addr = (Connection.HOST, Connection.PORT)

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(addr)

        receive_thread = Thread(target=self.receive)
        receive_thread.start()

    def on_closing(self, event=None):
        """This function is to be called when the window is closed."""
        if self.client_socket:
            self.send({QUIT: True})
        self.top.destroy()

    def receive(self):
        """Handles receiving of messages."""
        while True:
            try:
                rcvd = self.client_socket.recv(BUFSIZ).decode("utf8")
                print(f"received message: \n{rcvd}")
                msgs = rcvd.split(MESSAGE_SEPARATOR)
                for msg in msgs:
                    if msg.startswith(PRIVATE_MSG_PREFIX):
                        msg = msg.replace(PRIVATE_MSG_PREFIX, "")
                        self.private_msg_box_str.set(msg)
                    elif msg.startswith(PUBLIC_MSG_PREFIX):
                        msg = msg.replace(PUBLIC_MSG_PREFIX, "")
                        self.public_msg_box_str.set(msg)
                    elif msg.startswith(PLAYER_LIST_MSG_PREFIX):
                        msg = msg.replace(PLAYER_LIST_MSG_PREFIX, "")
                        self.player_list_box_str.set(msg)
                    elif msg.startswith(SET_PLAYER):
                        self.game_move_section.components[3].configure(text="Zuschauen", command=self.set_spectator)
                    elif msg.startswith(SET_SPECTATOR):
                        self.game_move_section.components[3].configure(text="Mitspielen", command=self.set_player)
                    elif msg.startswith(QUIT):
                        return
                    else:
                        print(f"message neither public nor private: {msg}")
            except OSError as e:  # Possibly client has left the chat.
                print(f"OSError: {e}")
                return

    def send(self, msg: dict):
        """
        :param msg: dictionary (json)
        """
        self.client_socket.send(bytes(MESSAGE_SEPARATOR+json.dumps(msg), "utf8"))
        
    def set_name(self, event=None):  # event is passed by binders. (???)
        """Sends the initial "name" message."""
        name = self.entry_str.get()
        self.send({SET_NAME: name})  # maybe it would be neater to have a prefix for this as well?
        self.entry_field.destroy()
        
    # Game interactions:
    def roll_dice(self, event=None):  # event is passed by binders.
        msg = {"ROLL_DICE": True}
        self.send(msg)

    def pass_dice(self, event=None):  # event is passed by binders.
        msg = {"PASS_DICE": True}
        self.send(msg)

    def reveal_dice(self, event=None):  # event is passed by binders.
        msg = {"REVEAL_DICE": True}
        self.send(msg)

    def set_player(self, event=None):  # event is passed by binders.
        msg = {SET_PLAYER: True}
        self.send(msg)

    def set_spectator(self, event=None):  # event is passed by binders.
        msg = {SET_SPECTATOR: True}
        self.send(msg)
        
    def __init__(self):

        self.client_socket = None

        self.top = tkinter.Tk()
        self.top.title("Mäxxchen")
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)

        # various strings used by the application:
        self.public_msg_box_str = tkinter.StringVar()
        self.public_msg_box_str.set("Willkommen bei Maxxchen!")
        self.player_list_box_str = tkinter.StringVar()
        self.player_list_box_str.set("...")
        self.private_msg_box_str = tkinter.StringVar()
        self.private_msg_box_str.set("Bitte Host-IP eingeben!")
        self.entry_str = tkinter.StringVar()
        self.entry_str.set(DEFAULT_ADDRESS)

        # Message Box:
        self.msg_section: App.AppSection = App.AppSection(top=self.top, orientation=tkinter.TOP, fill=tkinter.BOTH)
        self.msg_section.add_message(textvariable=self.public_msg_box_str)
        self.msg_section.add_message(textvariable=self.player_list_box_str)
        self.msg_section.add_message(textvariable=self.private_msg_box_str)
        self.entry_field: tkinter.Entry = self.msg_section.add_entry(textvariable=self.entry_str)
        self.entry_field.bind("<Return>", self.set_name)

        # Game Moves:
        self.game_move_section: App.AppSection = App.AppSection(top=self.top, orientation=tkinter.LEFT)
        self.game_move_section.add_button(text="Würfeln", command=self.roll_dice)
        self.game_move_section.add_button(text="Verdeckt weitergeben", command=self.pass_dice)
        self.game_move_section.add_button(text="Aufdecken", command=self.reveal_dice)
        self.game_move_section.add_button(text="Mitspielen", command=self.set_player)

        # Execute app and connect to server
        self.connect()


if __name__ == "__main__":

    Connection.setup()
    tkinter.mainloop()
    # tkinter mainloop stops after Connection app is destroyed
    app = App()
    tkinter.mainloop()

