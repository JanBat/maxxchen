#!/usr/bin/env python3
"""Modified Script for Tkinter GUI chat client."""

from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter
import json


# ###########<MESSAGING>################## #
# @ used as separator-prefix (in case buffer fills up with more than 1 message) TODO: use jsons instead
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

# ###########</MESSAGING>################# #

# ###########<GAME CONFIG>################ #
COLOR_BACKGROUND = 'gainsboro'
COLOR_MESSAGE_1 = 'whitesmoke'
COLOR_MESSAGE_2 = 'ghostwhite'
COLOR_ROLL = 'dodgerblue'
COLOR_DICE = 'tomato'
COLOR_PLAY = 'lime'
COLOR_REVEAL = 'gold'
GAME_TITLE = "Mäxxchen"
GAME_DEFAULT_RESOLUTION = "650x400"
# ###########</GAME CONFIG>############### #
BUFSIZ: int = 1024
DEFAULT_ADDRESS: str = "192.168.1.10"
DEFAULT_PORT: int = 63001
FONT ='Helvetica 10 bold'

DICE_RESULTS = [(3, 1), (3, 2), (4, 1), (4, 2), (4, 3), (5, 1), (5, 2), (5, 3), (5, 4), (6, 1), (6, 2), (6, 3), (6, 4),
                (6, 5), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (2, 1)]
TOGGLE_DICE = False
class Connection:
    """handles collection and storage of connection data (port+host). does not actually connect to anything"""
    PORT = ""
    HOST = ""

    @classmethod
    def setup(cls):
        """collect PORT and HOST information as user input in separate mini app"""

        connection_app = tkinter.Tk()
        connection_app.title("Mäxxchen-Login")
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

        def _add_component(self, component, side=None, fill=None):
            self.components.append(component)
            component.pack(side=side if side else self.orientation, fill=fill if fill else self.fill)
            self.frame.pack()

        def add_button(self, text: str, command, top=None, color=COLOR_BACKGROUND, font=FONT, height=3, width=20, side=None, fill=None ):
            print(f"Adding button: {text} \n {color}")
            new_button: tkinter.Button = tkinter.Button(top if top else self.frame, font=font, text=text, command=command, height=height, width=width, bg=color)
            self._add_component(new_button, side=side, fill=fill)
            return new_button

        def add_entry(self, textvariable: tkinter.StringVar, font=FONT):
            new_entry: tkinter.Entry = tkinter.Entry(self.frame, textvariable=textvariable, font=font)
            self._add_component(new_entry)
            return new_entry

        def add_message(self, textvariable: tkinter.StringVar, relief=tkinter.RAISED, width=500, color=COLOR_MESSAGE_1, font=FONT):
            msg = tkinter.Message(self.frame, textvariable=textvariable, relief=relief, bg=color, font=font, width=width)
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
                msgs = [l for l in rcvd.split(MESSAGE_SEPARATOR) if l]
                for msg in msgs:
                    msg_as_json = json.loads(msg)
                    for key in msg_as_json:
                        if key == PRIVATE_MSG_PREFIX:  # TODO: maybe stop this elif chain madness-in-the-making and use a dictionary instead
                            self.private_msg_box_str.set(msg_as_json[key])
                        elif key == PUBLIC_MSG_PREFIX:
                            self.public_msg_box_str.set(msg_as_json[key])
                        elif key == PLAYER_LIST_MSG_PREFIX:
                            self.player_list_box_str.set(msg_as_json[key])
                        elif key == DICE_MSG_PREFIX:
                            if TOGGLE_DICE:
                                self.dice_section.activate()
                            self.private_msg_box_str.set(msg_as_json[key])
                        elif key == SET_PLAYER:  # targetting the button via index 2 is super hacky (TODO: maybe fix)
                            self.game_move_section.components[1].configure(text="Zuschauen", command=self.set_spectator)
                        elif key == SET_SPECTATOR:
                            self.game_move_section.components[1].configure(text="Mitspielen", command=self.set_player)
                        elif key == QUIT:
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
        self.client_socket.send(bytes(json.dumps(msg), "utf8"))
        
    def set_name(self, event=None):  # event is passed by binders. (???)
        """Sends the initial "name" message."""
        name = self.entry_str.get()
        self.send({SET_NAME: name})  # maybe it would be neater to have a prefix for this as well?
        self.entry_field.destroy()
        
    # Game interactions:

    def declare_dice(self, declaration, event=None):
        msg = {DICE_MSG_PREFIX: declaration}
        self.send(msg)
        if TOGGLE_DICE:
            self.dice_section.deactivate()

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
        self.top.title(GAME_TITLE)
        self.top.geometry(GAME_DEFAULT_RESOLUTION)
        self.top.configure(bg=COLOR_BACKGROUND)
        self.top.resizable(width=0, height=1)
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)

        # various strings used by the application:
        self.public_msg_box_str = tkinter.StringVar()
        self.public_msg_box_str.set("Willkommen bei Mäxxchen!")
        self.player_list_box_str = tkinter.StringVar()
        self.player_list_box_str.set("...")
        self.private_msg_box_str = tkinter.StringVar()
        self.private_msg_box_str.set("Bitte Host-IP eingeben!")
        self.entry_str = tkinter.StringVar()
        self.entry_str.set("<hier Name eingeben>")  # TODO: random names?

        # Message Box:
        self.msg_section: App.AppSection = App.AppSection(top=self.top, orientation=tkinter.TOP, fill=tkinter.BOTH)
        self.msg_section.add_message(textvariable=self.public_msg_box_str, color=COLOR_MESSAGE_1)
        self.msg_section.add_message(textvariable=self.player_list_box_str, color=COLOR_MESSAGE_2)
        self.msg_section.add_message(textvariable=self.private_msg_box_str, color=COLOR_MESSAGE_1)
        self.entry_field: tkinter.Entry = self.msg_section.add_entry(textvariable=self.entry_str)
        self.entry_field.bind("<Return>", self.set_name)



        # Game Moves:
        self.game_move_section: App.AppSection = App.AppSection(top=self.top, orientation=tkinter.LEFT)
        self.game_move_section.add_button(text="Würfeln", command=self.roll_dice, color=COLOR_ROLL)
        #self.game_move_section.add_button(text="Verdeckt weitergeben", command=self.pass_dice, color=COLOR_DICE)
        self.game_move_section.add_button(text="Mitspielen", command=self.set_player, color=COLOR_PLAY)
        self.game_move_section.add_button(text="Aufdecken", command=self.reveal_dice, color=COLOR_REVEAL)

        # Dice Selection Box:   (here be Spaghetti Monsters)
        self.dice_section: App.AppSection = App.AppSection(top=self.top, orientation=tkinter.TOP)
        for i in [0, 7, 14]:  # Dörthe says hi
            subsection = tkinter.Frame(self.dice_section.frame)
            self.dice_section._add_component(subsection)
            for die in DICE_RESULTS[i:i+7]:
                self.dice_section.add_button(text=str(f"({die[0]}/{die[1]})"), top=subsection, command=lambda d=die: self.declare_dice(d), color=COLOR_DICE,
                                             height=3, width=3, side=tkinter.LEFT)

        if TOGGLE_DICE:
            self.dice_section.deactivate()
        # Execute app and connect to server
        self.connect()


if __name__ == "__main__":

    Connection.setup()
    tkinter.mainloop()
    # tkinter mainloop stops after Connection app is destroyed
    app = App()
    tkinter.mainloop()

