# maxxchen
As suggested by popular demand, bringing you the latest in dice game technology. Maybe we learn something about sockets in the process. 

to use:

- install [Python](https://www.python.org/downloads/ "Just pick the latest version =)")
- have 1 person run the [serverscript](https://raw.githubusercontent.com/JanBat/maxxchen/main/server.py)(execute via python); this person also needs to
    - activate port forwarding to port 63001 in their home router
    - possibly create an exception for port 63001 / the running server python application in their firewall
- have everyone else start the [clientscript](https://raw.githubusercontent.com/JanBat/maxxchen/main/client.pyw) via python, type in host's ip and port 63001
- after that the actual game app should start, pick a name and start playing! :D
