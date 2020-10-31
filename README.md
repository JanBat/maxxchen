# Mäxxchen
As suggested by popular demand, bringing you the latest in dice game technology. Maybe we learn something about sockets in the process. 

to use:

- install [Python](https://www.python.org/downloads/ "Just pick the latest version =)") or use the `.exe`files (download [client](https://github.com/JanBat/maxxchen/raw/main/M%C3%A4xchen-Client.exe)/[server](https://github.com/JanBat/maxxchen/raw/main/M%C3%A4xchen-Server.exe)) in Windows, courtesy of [this lovely repo](https://github.com/brentvollebregt/auto-py-to-exe)
- have 1 person run the [serverscript](https://raw.githubusercontent.com/JanBat/maxxchen/main/server.py)(execute via python); this person also needs to
    - activate port forwarding in their home router of port 63001 to their local machine
    - possibly create an exception for port 63001 / the running server python application in their firewall
- have everyone else start the [clientscript](https://raw.githubusercontent.com/JanBat/maxxchen/main/client.pyw) via python, type in host's IPv4 ip [(how to find your global IP)](https://www.google.com/search?q=what+is+my+ip "") and port 63001
- after that the actual game app should start, pick a name and start playing! :D
