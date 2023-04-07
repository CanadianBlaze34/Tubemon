import socket
import pickle
from _thread import start_new_thread
import logging, traceback
from typing import Any
from settings import *
from network import dict_to_str_bytes, str_to_dict

clients : int = None
client_data : dict[int, dict[Any]] = {}


def update_reply_w_other_clients_data(client_id : int, ACTION_ID : int, data_dict : dict[int, dict[Any]], reply_dict : dict[int, dict[Any]]) -> bool:
    updated : bool = False
    # send other clients positions
    # BUG: not race condition safe
    for client in client_data.keys():
        # don't add this clients position to the reply,
        # as the client already knows it's position
        if client == client_id:
            continue
        updated = True
        if not reply_dict.get(client):
            reply_dict[client] = {ACTION_ID: client_data[client][ACTION_ID]}
        else:
            reply_dict[client][ACTION_ID] = client_data[client][ACTION_ID]
    return updated

def thread_client(client : socket.socket, ip_address : Any, client_id : int) -> None:

    global clients
    global client_data

    starting_position = (1226, 835)
    client_data[client_id] = {MOVEMENT_ID : starting_position}
    client.send(str(client_id).encode())

    try:

        while True:

            data = client.recv(BUFFER_SIZE)
            
            if not data:
                break
            #print(f'Received client data from {client_id}.')
            size_in_bytes : int = len(data)
            data_str : str = data.decode()
            #print(f'Client {client_id}:\n\t{data_str}\n\t{size_in_bytes} bytes')
            data_dict : dict[int, dict[int, Any]]= str_to_dict(data_str, '%', ':', '@')
            #print(f'Client {client_id}:\n\t{data_dict}')

            #print(f'Generating a reply for client {client_id}.')
            reply : dict[int, dict[Any]] = {}
            send_reply : bool = False # true if there is a reply
            if MOVEMENT_ID in data_dict[client_id]:
                # update client movement 
                #print(f'Client {client_id} sent movement data.')
                #print(f'Updating client {client_id} movement data.')
                client_data[client_id][MOVEMENT_ID] = data_dict[client_id][MOVEMENT_ID]
                # update the reply with other clients data
                #print(f'Generating a movement data reply for client {client_id}.')
                send_reply |= update_reply_w_other_clients_data(client_id, MOVEMENT_ID, data_dict, reply)
            
            if ATTACK_ID in data_dict:
                #send_reply |= update_other_clients_data(client_id,   ATTACK_ID, data_dict, reply)
                pass

            if send_reply:
                byte_reply = dict_to_str_bytes(reply)
                client.sendall(byte_reply)
                size_in_bytes = len(byte_reply)
                #print(f'Replying to client {client_id}')
                #print(f'Sending client {client_id}\n\t{reply}\n\t{byte_reply}\n\t{size_in_bytes} bytes')
            else:
                client.sendall(GRIZZLY_CO.encode())
                #print(f'No reply for client {client_id}.')

                        
    except ConnectionResetError:
        print(f'Client {ip_address} has closed the connection.')
    except:
        logging.error(traceback.format_exc())
    finally:
        client.close()
        client = None
        print(f'{ip_address} has been disconnected.')
        client_data.pop(client_id)
        clients -= 1

def server() -> None:
    # start a server
    server : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT)) # can throw exceptions
    server.listen(MAX_CONNECTIONS)
    print(f'Server started. Waiting for a connection on {SERVER} at port {PORT}.')

    # initialize variables
    global clients
    clients = 0

    # main loop
    while True:

        # halt the main server thread until a client can join
        client, ip_address = server.accept()
        print(f'{ip_address[0]} has been connected.')

        start_new_thread(thread_client, (client, ip_address[0], clients))

        clients += 1

    # finished
    server.close()

if __name__ == '__main__':
    try:
        server()
    except:
        logging.error(traceback.format_exc())
    finally:
        # halt the terminal so errors can be viewed
        print('Press \'Enter\' to the close Console.')
        input()