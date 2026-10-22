# -*- coding: utf-8 -*-
"""
Revit MCP In-Process Listener
Enables real-time Model Context Protocol (MCP) commands inside active Autodesk Revit session.
Architecture:
- Background HttpListener thread on http://127.0.0.1:8788/
- Thread-Safe Revit execution via IExternalEventHandler and ExternalEvent
Author: Dilupa & Antigravity
"""

import os
import sys
import json
import threading
import traceback
import io

import clr
clr.AddReference('System')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from System.Net import HttpListener
from System.Text import Encoding
from System.IO import StreamReader, StreamWriter
from Autodesk.Revit import DB, UI
from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent

PORT = 8799
_listener = None
_listener_thread = None
_external_event = None
_command_handler = None
_is_running = False

DEBUG_LOG = r"C:\Users\User\Documents\AntGvt_Dilu\mcp_debug.log"

def _log(msg):
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(str(msg) + "\n")
    except:
        pass


class RevitCommandHandler(IExternalEventHandler):
    """
    Executes Python scripts safely inside Revit's UI Thread context.
    Prevents thread violations and crashes.
    """
    def __init__(self):
        self.code_to_run = ""
        self.result = None
        self.error = None
        self.stdout = ""
        self.done_event = threading.Event()

    def Execute(self, uiapp):
        self.result = None
        self.error = None
        self.stdout = ""
        
        # Capture standard output
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        try:
            _log("Executing on Revit UI Thread...")
            app = uiapp.Application
            uidoc = uiapp.ActiveUIDocument
            doc = uidoc.Document if uidoc else None

            scope = {
                'uiapp': uiapp,
                'app': app,
                'uidoc': uidoc,
                'doc': doc,
                'DB': DB,
                'UI': UI,
                'RESULT': None
            }

            code_str = str(self.code_to_run)
            code_obj = compile(code_str, '<string>', 'exec')
            exec(code_obj, scope)

            self.result = scope.get('RESULT', 'SUCCESS')
            self.stdout = redirected_output.getvalue()
            _log("Execution completed successfully.")
        except Exception as ex:
            self.error = traceback.format_exc()
            self.stdout = redirected_output.getvalue()
            _log("Execution error: " + str(self.error))
        except:
            self.error = "Unknown .NET exception occurred"
            self.stdout = redirected_output.getvalue()
            _log("Execution unhandled .NET exception")
        finally:
            sys.stdout = old_stdout
            self.done_event.set()

    def GetName(self):
        return "RevitMcpCommandHandler"


def _handle_request(context):
    """Processes incoming HTTP requests from the MCP server."""
    global _command_handler, _external_event

    request = context.Request
    response = context.Response

    # Enable CORS
    response.Headers.Add("Access-Control-Allow-Origin", "*")
    response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.Headers.Add("Access-Control-Allow-Headers", "Content-Type")

    if request.HttpMethod == "OPTIONS":
        response.StatusCode = 200
        response.Close()
        return

    path = request.Url.AbsolutePath.lower().rstrip('/')
    resp_data = {}
    status_code = 200

    _log("Request received: {} {}".format(request.HttpMethod, path))

    try:
        body = ""
        if request.HasEntityBody:
            reader = StreamReader(request.InputStream, Encoding.UTF8)
            body = reader.ReadToEnd()
            reader.Close()

        if path == "" or path == "/ping":
            resp_data = {
                "status": "ok",
                "app": "Revit",
                "listener_port": PORT,
                "is_running": True
            }

        elif path == "/execute":
            req_json = json.loads(body) if body else {}
            code = req_json.get("code", "")

            if not code:
                resp_data = {"success": False, "error": "No 'code' parameter provided"}
                status_code = 400
            else:
                _command_handler.code_to_run = code
                _command_handler.done_event.clear()

                # Raise ExternalEvent to wake Revit UI thread
                raise_res = _external_event.Raise()
                _log("ExternalEvent.Raise() returned: {}".format(raise_res))

                # Wait for Revit thread to complete (timeout 60 seconds)
                completed = _command_handler.done_event.wait(60.0)

                if not completed:
                    resp_data = {"success": False, "error": "Execution timed out waiting for Revit UI thread."}
                    status_code = 504
                elif _command_handler.error:
                    resp_data = {
                        "success": False,
                        "error": _command_handler.error,
                        "stdout": _command_handler.stdout
                    }
                    status_code = 500
                else:
                    resp_data = {
                        "success": True,
                        "result": _command_handler.result,
                        "stdout": _command_handler.stdout
                    }

        else:
            resp_data = {"error": "Endpoint not found: {}".format(path)}
            status_code = 404

    except Exception as ex:
        _log("Handler exception: " + str(ex))
        resp_data = {"error": str(ex), "trace": traceback.format_exc()}
        status_code = 500
    except:
        _log("Handler unknown .NET exception")
        resp_data = {"error": "Unknown .NET exception"}
        status_code = 500

    try:
        resp_json = json.dumps(resp_data)
        response.ContentType = "application/json; charset=utf-8"
        response.StatusCode = status_code
        writer = StreamWriter(response.OutputStream, Encoding.UTF8)
        writer.Write(resp_json)
        writer.Flush()
        writer.Close()
        response.Close()
        _log("Response sent successfully for {}".format(path))
    except Exception as ex:
        _log("Write error: " + str(ex))
        try:
            response.Abort()
        except:
            pass
    except:
        _log("Write unknown error")
        try:
            response.Abort()
        except:
            pass


def _listener_loop():
    """Background loop listening for incoming HTTP connections."""
    global _listener, _is_running
    _log("Listener loop entered.")
    while _is_running and _listener and _listener.IsListening:
        try:
            context = _listener.GetContext()
            t = threading.Thread(target=_handle_request, args=(context,))
            t.daemon = True
            t.start()
        except Exception as ex:
            _log("Listener loop exception: " + str(ex))
            break
        except:
            _log("Listener loop unknown exception")
            break
    _log("Listener loop exited.")


def start_server():
    """Starts the Revit MCP In-Process Listener."""
    global _listener, _listener_thread, _external_event, _command_handler, _is_running

    if _is_running:
        return True, "Revit MCP Server is already running on port {}".format(PORT)

    try:
        _command_handler = RevitCommandHandler()
        _external_event = ExternalEvent.Create(_command_handler)

        _listener = HttpListener()
        _listener.Prefixes.Add("http://127.0.0.1:{}/".format(PORT))
        _listener.Start()

        _is_running = True
        _listener_thread = threading.Thread(target=_listener_loop)
        _listener_thread.daemon = True
        _listener_thread.start()

        _log("Server started on port {}".format(PORT))
        return True, "Revit MCP Server started successfully on http://127.0.0.1:{}/".format(PORT)
    except Exception as ex:
        _is_running = False
        _log("Start server error: " + str(ex))
        return False, "Failed to start Revit MCP Server: {}".format(str(ex))
    except:
        _is_running = False
        _log("Start server unknown error")
        return False, "Failed to start Revit MCP Server (System exception)"


def stop_server():
    """Stops the Revit MCP In-Process Listener."""
    global _listener, _is_running
    _is_running = False
    if _listener:
        try:
            _listener.Stop()
            _listener.Close()
        except:
            pass
        _listener = None
    _log("Server stopped.")
    return True, "Revit MCP Server stopped."


if __name__ == '__main__':
    success, msg = start_server()
    print(msg)
