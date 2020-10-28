#!/usr/bin/env python3
"""Modified Script for Tkinter GUI chat client."""
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter


############<GAME LOGIC>##################
# @ used as separator-prefix (in case buffer fills up with more than 1 message)
# to contain both client and server in their entirety in 1 script each,
# there's a copy of these constants in both files (not elegant, but hey)
MESSAGE_SEPARATOR = "@"
GAMESTATE_UPDATE_PREFIX = 'GAMESTATE_UPDATE_MSG: '
PRIVATE_MSG_PREFIX = 'PRIVATE: '
PUBLIC_MSG_PREFIX = 'PUBLIC: '
PLAYER_LIST_MSG_PREFIX = 'PLAYER_LIST: '
SET_PLAYER = "SET_PLAYER"
SET_SPECTATOR = "SET_SPECTATOR"
QUIT = "QUIT"

############</GAME LOGIC>#################
BUFSIZ = 1024
DEFAULT_ADDRESS = "192.168.1.10"

def receive():
    """Handles receiving of messages."""
    while True:
        try:
            rcvd = connection_data['client_socket'].recv(BUFSIZ).decode("utf8")
            print(f"received message: \n{rcvd}")
            msgs = rcvd.split("@")
            for msg in msgs:
                if msg.startswith(PRIVATE_MSG_PREFIX):
                    msg = msg.replace(PRIVATE_MSG_PREFIX, "")
                    App.private_msg_box_str.set(msg)
                elif msg.startswith(PUBLIC_MSG_PREFIX):
                    msg = msg.replace(PUBLIC_MSG_PREFIX, "")
                    App.public_msg_box_str.set(msg)
                elif msg.startswith(PLAYER_LIST_MSG_PREFIX):
                    msg = msg.replace(PLAYER_LIST_MSG_PREFIX, "")
                    App.player_list_box_str.set(msg)
                elif msg.startswith(SET_PLAYER):
                    App.game_move_section.components[3].configure(text="Zuschauen", command=set_spectator)
                elif msg.startswith(SET_SPECTATOR):
                    App.game_move_section.components[3].configure(text="Mitspielen", command=set_player)
                elif msg.startswith(QUIT):
                    return
                else:
                    print(f"message neither public nor private: {msg}")
        except OSError as e:  # Possibly client has left the chat.
            print(f"OSError: {e}")
            return


def roll_dice(event=None):  # event is passed by binders.
    msg = f"{GAMESTATE_UPDATE_PREFIX}ROLL_DICE"
    connection_data['client_socket'].send(bytes(msg, "utf8"))


def pass_dice(event=None):  # event is passed by binders.
    msg = f"{GAMESTATE_UPDATE_PREFIX}PASS_DICE"
    connection_data['client_socket'].send(bytes(msg, "utf8"))


def reveal_dice(event=None):  # event is passed by binders.
    msg = f"{GAMESTATE_UPDATE_PREFIX}REVEAL_DICE"
    connection_data['client_socket'].send(bytes(msg, "utf8"))


def set_player(event=None):  # event is passed by binders.
    msg = f"{GAMESTATE_UPDATE_PREFIX}{SET_PLAYER}"
    connection_data['client_socket'].send(bytes(msg, "utf8"))


def set_spectator(event=None):  # event is passed by binders.
    msg = f"{GAMESTATE_UPDATE_PREFIX}{SET_SPECTATOR}"
    connection_data['client_socket'].send(bytes(msg, "utf8"))


def on_closing(event=None):
    """This function is to be called when the window is closed."""
    if connection_data['client_socket']:
        connection_data['client_socket'].send(bytes(QUIT, "utf8"))
    top.quit()


def set_host(event=None):
    connection_data["HOST"] = my_msg.get()
    my_msg.set("63001")
    entry_field.bind("<Return>", set_port)
    private_msg_box_str.set("Bitte Port eingeben!")


def set_port(event=None):
    connection_data["PORT"] = my_msg.get()
    my_msg.set("TestName1")
    entry_field.bind("<Return>", set_name)
    connect()

def set_name(event=None):  # event is passed by binders.
    """Sends the initial "name" message."""
    msg = my_msg.get()
    my_msg.set("")  # Clears input field.
    connection_data['client_socket'].send(bytes(msg, "utf8"))
    entry_field.destroy()

def connect():
    if not connection_data["PORT"]:
        connection_data["PORT"] = 63001
    else:
        connection_data["PORT"] = int(connection_data["PORT"])


    ADDR = (connection_data["HOST"], connection_data["PORT"])

    connection_data['client_socket'] = socket(AF_INET, SOCK_STREAM)
    connection_data['client_socket'].connect(ADDR)

    receive_thread = Thread(target=receive)
    receive_thread.start()


class App:  

    class AppSection:
        def __init__(self, top, orientation=tkinter.LEFT, fill=tkinter.NONE):
            self.components = []
            self.frame: tkinter.Frame = tkinter.Frame(top)
            self.orientation = orientation
            self.fill = fill

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
                component.pack()  # grid_forget ?

        def deactivate(self):
            for component in self.components:
                component.forget()  # grid_forget ?

    def __init__(self):

        self.connection_data ={
            "HOST": "",
            "PORT": "",
            "client_socket": None
        }

        top = tkinter.Tk()
        top.title("Mäxxchen")
        top.protocol("WM_DELETE_WINDOW", on_closing)

        # various strings used by the application:
        self.public_msg_box_str = tkinter.StringVar()
        self.public_msg_box_str.set("Willkommen bei Maxxchen!")
        self.player_list_box_str = tkinter.StringVar()
        self.player_list_box_str.set("...")
        self.private_msg_box_str = tkinter.StringVar()
        self.private_msg_box_str.set("Bitte Host-IP eingeben!")
        self.entry_str = tkinter.StringVar()
        self.entry_str.set(DEFAULT_ADDRESS)

        # Game Moves:
        self.game_move_section: App.AppSection = App.AppSection(top=top, orientation=tkinter.LEFT)
        self.game_move_section.add_button(text="Würfeln", command=roll_dice)
        self.game_move_section.add_button(text="Verdeckt weitergeben", command=pass_dice)
        self.game_move_section.add_button(text="Aufdecken", command=reveal_dice)
        self.game_move_section.add_button(text="Mitspielen", command=set_player)

        # Message Box:
        self.msg_section: App.AppSection = App.AppSection(top=top, orientation=tkinter.TOP, fill=tkinter.BOTH)
        self.msg_section.add_message(textvariable=self.public_msg_box_str)
        self.msg_section.add_message(textvariable=self.player_list_box_str)
        self.msg_section.add_message(textvariable=self.private_msg_box_str)
        self.entry_field: tkinter.Entry = self.msg_section.add_entry(textvariable=self.entry_str)
        self.entry_field.bind("<Return>", set_host)


if __name__ == "__main__":
    app = App()
    tkinter.mainloop()
