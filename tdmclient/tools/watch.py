#!/usr/bin/env python3
# Yves Piguet, Feb 2021

from tdmclient import ClientAsync

if __name__ == "__main__":

    with ClientAsync(debug=1) as client:

        async def prog():
            await client.wait_for_node()
            node_id_str = client.first_node()["node_id_str"]
            await client.watch(node_id_str)
            while True:
                await client.sleep(1)

        client.run_async_program(prog)
