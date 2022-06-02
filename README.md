# ADSD-SPC-PR
Exam project for "Architetture dei Sistemi Distribuiti" university course @ UniCampus Rome - Developed by Paolo Ruggirello & Simone Pio Caronia.


# Broker tree management

Exam track chosen:

> Estendere il broker per permetterne un utilizzo distribuito. In particolare:
> - la connessione tra i broker componenti deve essere ad albero
> - la struttura è completamente trasparente al generico client che può connettersi a uno qualsiasi dei broker componenti
> - si lascia completa libertà sulla gestione dinamica dei broker in ingresso e uscita

Following the track above, the solution designed proposed an implementation that can be summarised in the following points:
- all structure is handled by a supervisor. It exposes some services which are used to register to network, confirm new node, notify down nodes and get available broker;
- each broker of the tree network is able to receive both new broker, which is added to tree network and confirmed by the father broker, and clients to let them subscribe/unsubscribe to topic and send messages on it;
- the cmd client (and gui version, more info on Clients paragraph) present on the main folder which receives from supervisor a broker from the entire tree to connect and communicate.


# Entities

## Supervisor
The supervisor (supervisor.py) has the manager role in tree structure. It is the only resposible to insert/remove and modify the tree.
It exposes both a REST and TCP server.
### REST
The REST server has been implemented using the framework Flask. The services exposed via endpoints are responsible to inform about tree structure and made change on it.

### TCP
Supervisor can be seen as tree root's father. The TCP connection is needed to obtain the port of the root broker and listen on its state.
Supervisor TCP server confirms only one connection at time.

## Broker

## Clients


# Installing and setup



