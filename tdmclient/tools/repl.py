# This file is part of tdmclient.
# Copyright 2021-2022 ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE,
# Miniature Mobile Robots group, Switzerland
# Author: Yves Piguet
#
# SPDX-License-Identifier: BSD-3-Clause

import sys
import getopt

from tdmclient import ClientAsync, TDMConsole

try:
    # line edition and history if available
    import readline
    # name completion if available
    import rlcompleter
    readline.parse_and_bind('tab:complete')
except ModuleNotFoundError:
    pass


def help():
    print(f"""Usage: python3 -m tdmclient repl [options]
Read-eval-print loop with link and synchronization with Thymio

Options:
  --help         display this help message and exit
  --password=PWD specify password for remote tdm
  --robotid=I    robot id; default=any
  --robotname=N  robot name; default=any
  --tdmaddr=H    tdm address (default: localhost or from zeroconf)
  --tdmport=P    tdm port (default: 8596 (tcp) or 8597 (ws), or from zeroconf)
  --tdmws        connect to tdm with WebSocket (default: plain TCP)
  --zeroconf     use zeroconf (default: no zeroconf)
""")


def main(argv=None, tdm_transport=None):
    zeroconf = False
    tdm_addr = None
    tdm_port = None
    tdm_ws = False
    password = None
    robot_id = None
    robot_name = None

    if argv is not None:
        try:
            arguments, values = getopt.getopt(argv[1:],
                                              "",
                                              [
                                                  "help",
                                                  "password=",
                                                  "robotid=",
                                                  "robotname=",
                                                  "tdmaddr=",
                                                  "tdmport=",
                                                  "tdmws",
                                                  "zeroconf",
                                              ])
        except getopt.error as err:
            print(str(err))
            return 1
        for arg, val in arguments:
            if arg == "--help":
                help()
                return 0
            elif arg == "--password":
                password = val
            elif arg == "--robotid":
                robot_id = val
            elif arg == "--robotname":
                robot_name = val
            elif arg == "--tdmaddr":
                tdm_addr = val
            elif arg == "--tdmport":
                tdm_port = ClientAsync.DEFAULT_TDM_PORT if val == "default" else int(val)
            elif arg == "--tdmws":
                tdm_ws = True
            elif arg == "--zeroconf":
                zeroconf = True

    with ClientAsync(zeroconf=zeroconf,
                     tdm_addr=tdm_addr, tdm_port=tdm_port, tdm_ws=tdm_ws,
                     tdm_transport=tdm_transport,
                     password=password) as client:

        async def co_init():
            with await client.lock(node_id=robot_id, node_name=robot_name) as node:
                interactive_console = TDMConsole(user_functions={
                    "get_client": lambda: client,
                    "get_node": lambda: node,
                })
                await interactive_console.init(client, node)
                interactive_console.interact()

        client.run_async_program(co_init)
