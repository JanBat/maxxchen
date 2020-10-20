#!/usr/bin/env python3
"""Script for Tkinter GUI chat client."""
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter


############<GAME LOGIC>##################
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
                    private_msg_box_str.set(msg)
                elif msg.startswith(PUBLIC_MSG_PREFIX):
                    msg = msg.replace(PUBLIC_MSG_PREFIX, "")
                    public_msg_box_str.set(msg)
                elif msg.startswith(PLAYER_LIST_MSG_PREFIX):
                    msg = msg.replace(PLAYER_LIST_MSG_PREFIX, "")
                    player_list_box_str.set(msg)
                elif msg.startswith(SET_PLAYER):
                    player_button.configure(text="Zuschauen", command=set_spectator)
                elif msg.startswith(SET_SPECTATOR):
                    player_button.configure(text="Mitspielen", command=set_player)
                elif msg.startswith(QUIT):
                    return
                else:
                    print(f"message neither public nor private: {msg}")
                # public or private message?
                #msg_list.insert(tkinter.END, msg)
        except OSError:  # Possibly client has left the chat.
            return



'''
def set_name(event=None):  # event is passed by binders.
    """Handles sending of messages."""
    msg = my_msg.get()
    my_msg.set("")  # Clears input field.
    client_socket.send(bytes(f"{GAMESTATE_UPDATE_PREFIX}SET_NAME{msg}", "utf8"))
'''
def roll_dies(event=None):  # event is passed by binders.
    msg = f"{GAMESTATE_UPDATE_PREFIX}ROLL_DICE"
    connection_data['client_socket'].send(bytes(msg, "utf8"))

def pass_dies(event=None):  # event is passed by binders.
    msg = f"{GAMESTATE_UPDATE_PREFIX}PASS_DICE"
    connection_data['client_socket'].send(bytes(msg, "utf8"))

def reveal_dies(event=None):  # event is passed by binders.
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
    entry_field.bind("<Return>", set_PORT)
    private_msg_box_str.set("Bitte Port eingeben!")

def set_PORT(event=None):
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

top = tkinter.Tk()
top.title("Maxxchen")

messages_frame = tkinter.Frame(top)
my_msg = tkinter.StringVar()  # For the messages to be sent.
my_msg.set("--blank default message--")

public_msg_box_str = tkinter.StringVar()
public_msg_box = tkinter.Message(messages_frame, textvariable=public_msg_box_str, relief=tkinter.RAISED, width=500)  # non-scrolly gamestate display (?)
public_msg_box_str.set("Willkommen bei Maxxchen!")
public_msg_box.pack(side=tkinter.TOP, fill=tkinter.BOTH)

private_msg_box_str = tkinter.StringVar()
private_msg_box = tkinter.Message(messages_frame, textvariable=private_msg_box_str, relief=tkinter.RAISED, width=500)  # non-scrolly gamestate display (?)
private_msg_box_str.set("Bitte Host-IP eingeben!")
private_msg_box.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH)

player_list_box_str = tkinter.StringVar()
player_list_box = tkinter.Message(messages_frame, textvariable=player_list_box_str, relief=tkinter.RAISED, width=500)  # non-scrolly gamestate display (?)
player_list_box_str.set("...")
player_list_box.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH)

messages_frame.pack()

entry_field = tkinter.Entry(top, textvariable=my_msg)
#entry_field.bind("<Return>", set_host)
entry_field.pack()
roll_button = tkinter.Button(top, text="Würfeln", command=roll_dies)
roll_button.pack(side=tkinter.LEFT)
pass_button = tkinter.Button(top, text="Verdeckt weitergeben", command=pass_dies)
pass_button.pack(side=tkinter.LEFT)
reveal_button = tkinter.Button(top, text="Aufdecken", command=reveal_dies)
reveal_button.pack(side=tkinter.LEFT)
player_button = tkinter.Button(top, text="Mitspielen", command=set_player)
player_button.pack(side=tkinter.LEFT)
# name_button = tkinter.Button(top, text="Set Name", command=set_name)
# name_button.pack()



top.protocol("WM_DELETE_WINDOW", on_closing)

#----Now comes the sockets part----
my_msg.set("")

connection_data = {
    "HOST": "",
    "PORT": "",
    "client_socket": None
}




entry_field.bind("<Return>", set_host)
my_msg.set("192.168.1.10")
#PORT = input('Enter port: ')


tkinter.mainloop()  # Starts GUI execution.