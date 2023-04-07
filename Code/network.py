import socket
import ast
#import pickle
import logging, traceback
from settings import *
from typing import Any
import select

class Network:

    def __init__(self) -> None:
        self.server    : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_id : Any           = -1
        self.connected : bool          = False

    def connect(self) -> bool:
        try:
            self.server.connect((SERVER, PORT))
            self.client_id = self.server.recv(BUFFER_SIZE).decode() # Server will send the player id first
            print(f'\'Network.connect()\': client id #{self.client_id} connected to {SERVER}')

            self.connected = True
        except:
            logging.error(traceback.format_exc())
            self.connected = False

        return self.connected

    def send(self, data : bytes) -> None:
        #data_in_bytes : bytes = pickle.dumps(data)
        bytes_num     : int   = self.server.send(data)

        if bytes_num != len(data):
            print(f'\'Network.send()\': client id # {self.client_id} could not send all data.')

    def send_all(self, data : bytes) -> None:
        #try:
            #data_in_bytes : bytes = pickle.dumps(data)
            #data_missing : Any = 
        self.server.sendall(data)

            #if data_missing: print(f'\'Network.send_all()\': client id # {self.client_id} could not send all data.')
        #except: logging.error(traceback.format_exc())

    def receive(self) -> tuple[bytes, bool]:
        try:
            #return pickle.loads(self.client.recv(BUFFER_SIZE))
            #return self.server.recv(BUFFER_SIZE)
            read, _, _ = select.select([self.server], [], [], None) # read list, write list, error list, timeout
            if read:
                return (self.server.recv(BUFFER_SIZE), self.connected)
        except:
            self.connected = False
            logging.error(traceback.format_exc())
        return (None, self.connected)
    

    def disconnect(self) -> None:
        self.server.close()
        self.connected = False
        print(f'\'Network.disconnect()\': client id #{self.client_id} disconnected from {SERVER}')
    
def dict_to_str_bytes(dictionary : dict[int, dict[int, Any]]) -> bytes:
        
    dict_str : str = ''
    a = ':' # action delim
    v = '@' #  value delim
    c = '%' # client delim

    for client_id in dictionary.keys():

        dict_str += f'{client_id}'

        for action_id in dictionary[client_id].keys():
            dict_str += f'{a}{action_id}{v}{dictionary[client_id][action_id]}'

        dict_str += c

    # '0:0@(4,2):3@True:2@4%4:0@(12,36)'
    #        int:  literal@         Any,      int
    # 'client_id:action_id@action_value%client_id'
    # remove trailing '%'
    return (dict_str[:-1]).encode()

def str_to_dict(o_str : str, delim_1 : str = '%', delim_2 : str = ':', delim_3 : str = '@') -> dict[int, dict[int, Any]]:
    
    # str to dict with int keys
    
    client_data : list[str] = o_str.split(delim_1)
    new_dict : dict[int, dict[int, any]] = {}

    for data in client_data:
        
        # client_id, action_id and action values
        ci_ai_av : list[str] = data.split(delim_2)
        client_id : int = int(ci_ai_av[0])
        new_dict[client_id] = {}
        # remove the client id from the array
        # action ids and action values
        ais_avs = ci_ai_av[1:]

        # action id and action value
        for ai_av in ais_avs:

            # key and value
            k_v : list[str] = ai_av.split(delim_3)
            # convert action id to proper type
            k_v[0] = int(k_v[0])
            # convert action value to proper type
            k_v[1] = ast.literal_eval(k_v[1])
            # save
            new_dict[client_id][k_v[0]] = k_v[1]
    
    return new_dict

