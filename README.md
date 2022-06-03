# ADSD-SPC-PR
Exam project for "Architetture dei Sistemi Distribuiti" university course @ UniCampus Rome - Developed by Paolo Ruggirello & Simone Pio Caronia.


# Broker tree management

Exam track chosen from https://github.com/vollero/asdsw2022/tree/main/elaborati:

> Estendere il broker per permetterne un utilizzo distribuito. In particolare:
> - la connessione tra i broker componenti deve essere ad albero
> - la struttura è completamente trasparente al generico client che può connettersi a uno qualsiasi dei broker componenti
> - si lascia completa libertà sulla gestione dinamica dei broker in ingresso e uscita

Following the track above, the solution designed proposes an implementation that can be summarised into the following points:
- all structure is handled by a supervisor (oracle). It exposes some services which are used to register to network, confirm new node, notify down nodes and get available broker;
- each broker of the tree network is able to receive both new broker, which is added to tree network and confirmed by the father broker, and clients to let them subscribe/unsubscribe to topic and send messages on it;
- the cmd client (and gui version, more info on Clients paragraph), present on the main folder, receives from supervisor a broker from the entire tree to connect and communicate.


# Entities
In order to achieve the structure above, we realized a three entities model:

## Supervisor
The supervisor (supervisor.py) has the manager role in tree structure. It is the only resposible to insert/remove and modify the tree.
It exposes both a REST and TCP server.
### REST
The REST server has been implemented using the framework Flask. The services exposed via endpoints are responsible to inform about tree structure and made change on it.

### TCP
Supervisor can be seen as tree root's father. The TCP connection is needed to obtain the port of the root broker and listen on its state.
Supervisor TCP server confirms only one connection at time.

## Broker
The Broker (broker.py) asks to the supervisor his father id in order to connect to the network. After that it starts a tcp server in order to accept tcp connections from clients and from other brokers.
When a broker receives a [SEND] command to a specific topic, it send the message to all the clients connected to him and also to other brokers in order to propagate the message in the network.  

## Clients
The clients developed are able to communicate with supervisor that should be instantiating in the same machine with REST server listening on port 10000 (as is by default to not make any changes on code. Anyway the REST server is available in external network). They request for an available broker using the dedicated endpoint and send the right commands to brokers. 
Two versions have been implemented:

### CMD
The cmd client (client_tcp_cmd.py) is a useful prompt client that can be used to connect to a broker and to send messages over the tree network. It has been created to let user interact with broker network as easier as possible.

### GUI
The GUI version has been created using framework Flutter (which uses Dart as programming language).
Link of repository (present also linux build on main folder): https://github.com/spioc999/adsd-spc-pr-client-gui

# Installing, setup and running

### Virtual Environment
We suggest you to create a dedicated virtual environment before start the execution.
If you don't want to create it then just skip this section.

To create the virtual environment follow these steps:
1. Go to the project's root directory
2. Create a folder named venv
3. Create the virtual environment with the following command:
> python3 -m venv venv/

4. Activate it:
> source venv/bin/activate

### Installing dependencies
To install all the needed dependencies you just need to run:
> pip install requirements.txt

N.B. Remember to activate your virtual environment if you have it.

### Start supervisor
To start the supervisor run:
> python3 supervisor.py

If you want to run it with a specific TCP server port then type:
> python3 supervisor.py -sp \<port\>
  
### Start broker
To start the broker type:
> python3 broker.py

If you want to run it with a specific TCP server port then type:
> python3 broker.py -sp \<port\>

If you have a linux-based os (like linux or macOs) and you also have a virtual enviroment, then you can use the "starter" script to run more than one broker at the same time.
To do it just type:
> ./starter.py

### Start prompt client
To start the prompt client type:
> python3 client_tcp_cmd.py

If you want to receive some instructions on how to use it, type \<help\> command.


### Start GUI client
To start the GUI client, just go to repository reported above, and, with a linux machine just download and exatract the .tar.gz file.
NOTE: do not move the application outside of bundle folder and do not delete data and lib folders inside of it.
