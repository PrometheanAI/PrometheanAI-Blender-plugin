import socket
import queue

from numpy import block

#Multiprocessing Vars
message_queue = None
response_queue = None

#Server Vars
server_socket = None
host = "127.0.0.1"
port = 1317
vacate_socket_command = 'promethean_vacate_socket'
enable_command_queue = True
ignore_vacate_socket = False

def start_server():
    global server_socket

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(5)

    server_loop()

def close_server():
    global server_socket

    if server_socket:
        server_socket.close()
        server_socket = None

def handle_response(connection_):
    #wait for response from blender
    while True:
        try:
            response = response_queue.get(block=False)
            if response == "ERROR":
                print("PrometheanAI: Received Error from DCC")
                break
            print("Response: " + str(response))
            connection_.sendall(response.encode())
            pass
            break
        except queue.Empty:
            pass
        except Exception as e:
            print("Promethean AI: Error handling response: " + str(e))

def handle_incoming_message(connection_):
    global message_queue

    while True:
        try:
            data = connection_.recv(131072)
            if data:
                if data.decode() == vacate_socket_command:
                    if not ignore_vacate_socket:
                        print("PrometheanAI: Received a Vacate Socket Command. Disconnecting")
                        close_server()
                        return
                else:
                    message_queue.put(data)
                    handle_response(connection_)
            else:
                break
        except Exception as e:
            print("PrometheanAI: Internal server error: " + str(e))
            pass

def server_loop():
    global server_socket
    
    print("PrometheanAI: Server Running")

    while server_socket:
        try:
            connection, addr = server_socket.accept()
            if enable_command_queue:
                #print("PrometheanAI: Got connection from " + str(addr))
                handle_incoming_message(connection)
        except:
            server_socket = None

def main(queue_, response_queue_):
    global message_queue
    global response_queue

    message_queue = queue_
    response_queue = response_queue_

    try:
        start_server()
    except Exception as e:
        error_message = "internal_server_error " + str(e)
        message_queue.put(error_message.encode())
