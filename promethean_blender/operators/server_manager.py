# Note: This file contains only code to manage the server subprocess. Not the actual server code, which can be found in 'server_process.py' 

from os import kill
import bpy

#Blender does not play nicely with threads, so we will use multiprocessing
import multiprocessing
import queue

import threading

from numpy import block

from bpy.app.handlers import persistent

from .. import command_manager, server_process
from ..constants import *

import atexit

process = None
message_queue = None
response_queue = None


def append_response(response):
    response_queue.put(response)

class ServerMessageModalOperator(bpy.types.Operator):
    """Operator which runs in a timer, to check for messages from the server subprocess"""
    bl_idname = SERVER_MESSAGE_MODAL_ID
    bl_label = SERVER_MESSAGE_MODAL_NAME
    _timer = None

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        return {FINISHED}

    def modal(self, context, event):
        global message_queue
        global response_queue
        global process

        if process == None or message_queue == None:
            return self.cancel(context)
        else:
            try:
                data = message_queue.get(block=False)
                response = command_manager.handle_message(data)
                response_queue.put(response)

            except queue.Empty:
                pass
            except Exception as e:
                print(e)
                response_queue.put("ERROR")
                pass

            return {PASS_THROUGH}

    def execute(self, context):
        wm = context.window_manager

        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        print("PrometheanAI: Checking for messages")
        return {RUNNING_MODAL}

def kill_server_process():
    global process
    global message_queue
    global response_queue
    
    bpy.context.window_manager.promethean_server_status = PROMETHEAN_SERVER_STATUS_DISCONNECTED

    if process:
        process.terminate()
        process.join()
        print ('PrometheanAI: Killing server, exit code:', process.exitcode)

    process = None

    message_queue = None
    response_queue = None

class KillServer(bpy.types.Operator):
    """Kills the Promethean TCP Server"""
    bl_idname = KILL_SERVER_OPERATOR_ID
    bl_label = KILL_SERVER_NAME


    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        kill_server_process()
        return {'FINISHED'}


class StartServer(bpy.types.Operator):
    """Begins Promethean TCP Server"""
    bl_idname = BEGIN_SERVER_OPERATOR_ID
    bl_label = BEGIN_SERVER_NAME

    @classmethod
    def poll(cls, context):
        return True

    def try_vacate_socket(self, timeout = 1.0):
        from ..server_process import port
        import socket

        ip = "127.0.0.1"

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(timeout)

            client_socket.connect((ip, port))
            client_socket.send(VACATE_MESSAGE.encode())
            data = client_socket.recv(131072)
            print(data.decode())
            client_socket.close()
        except:
            pass
    
    def execute(self, context):
        global process
        global message_queue
        global response_queue


        self.try_vacate_socket(0.5)


        print("PrometheanAI: Starting Server Process")

        message_queue = multiprocessing.Queue()
        response_queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=server_process.main, args=(message_queue,response_queue))
        process.start()

        print("PrometheanAI: Server process created - process ID: " + str(process.pid))


        bpy.context.window_manager.promethean_server_status = PROMETHEAN_SERVER_STATUS_CONNECTED
        #invoke the timer modal (See: ServerMessageModalOperator)
        bpy.ops.wm.promethean_check_for_messages()
        return {'FINISHED'}

startup_executed = False

@persistent
def load_handler(dummy):
    global process

    # If the process already exists, we just have to run to modal loop to keep checking for messages again
    if process:
        bpy.ops.wm.promethean_check_for_messages()

def startup_handler():
    print("PrometheanAI: Launching server on startup")
    bpy.ops.promethean.begin_server()


def create_types():
    bpy.types.WindowManager.promethean_server_status = bpy.props.StringProperty(default=PROMETHEAN_SERVER_STATUS_DISCONNECTED)

launched_on_startup = False
def startup_timer():
    global launched_on_startup

    if not launched_on_startup:
        startup_handler()
        launched_on_startup = True

    bpy.app.timers.unregister(startup_timer)

def register():
    bpy.utils.register_class(ServerMessageModalOperator)
    bpy.utils.register_class(StartServer)
    bpy.utils.register_class(KillServer)
    create_types()

    atexit.register(kill_server_process)

    # If blender opens a new file, the promethean_check_for_messages operator will be stopped, so we have to restart it
    bpy.app.handlers.load_post.append(load_handler)
    bpy.app.handlers.load_factory_startup_post.append(load_handler)

    # Register a timer, after 5 seconds the server will launch
    bpy.app.timers.register(startup_timer, first_interval=5)

    

def unregister():

    #kill_server_process()
    bpy.app.handlers.load_post.remove(load_handler)
    atexit.unregister(kill_server_process)

    bpy.utils.unregister_class(KillServer)
    bpy.utils.unregister_class(StartServer)
    bpy.utils.unregister_class(ServerMessageModalOperator)
