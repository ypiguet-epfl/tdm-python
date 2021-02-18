# Yves Piguet, Feb 2021

from time import sleep, monotonic
from tdmclient import Client
import types


class ClientAsync(Client):

    DEFAULT_SLEEP = 0.1

    def __init__(self, **kwargs):
        super(ClientAsync, self).__init__(**kwargs)

    def first_node(self):
        return self.nodes[0] if len(self.nodes) > 0 else None

    @types.coroutine
    def sleep(self, duration):
        t0 = monotonic()
        while duration < 0 or monotonic() < t0 + duration:
            self.process_waiting_messages()
            sleep(self.DEFAULT_SLEEP
                  if duration < 0
                  else max(min(self.DEFAULT_SLEEP, t0 + duration - monotonic()),
                           self.DEFAULT_SLEEP / 1e3))
            yield

    @types.coroutine
    def wait_for_node(self):
        while True:
            if self.process_waiting_messages():
                node = self.first_node()
                if node is not None:
                    return
            else:
                sleep(self.DEFAULT_SLEEP)
            yield

    @types.coroutine
    def wait_for_status(self, expected_status):
        while True:
            if self.process_waiting_messages():
                node = self.first_node()
                if node is not None:
                    status = node["status"]
                    if status == expected_status:
                        return
            else:
                sleep(self.DEFAULT_SLEEP)
            yield

    @types.coroutine
    def send_msg_and_get_result(self, send_fun):
        """Call a function which sends a message and wait for its reply.

        Parameter: send_fun(request_id_notify)
        """

        result = None
        done = False
        def notify(r):
            nonlocal result
            nonlocal done
            result = r
            done = True
        send_fun(notify)
        while not done:
            yield
            sleep(self.DEFAULT_SLEEP)
            self.process_waiting_messages()
        return result

    @types.coroutine
    def lock_node(self, node_id_str):
        result = yield from self.send_msg_and_get_result(
            lambda notify:
                self.send_lock_node(node_id_str, request_id_notify=notify)
        )
        return result

    @types.coroutine
    def unlock_node(self, node_id_str):
        result = yield from self.send_msg_and_get_result(
            lambda notify:
                self.send_unlock_node(node_id_str, request_id_notify=notify)
        )
        return result

    @types.coroutine
    def lock(self, node_id_str=None):
        """Lock the specified node and return its node id as a string.
        Without node id argument, wait until the first node is available
        and use it.

        Should be used in a "with" construct which will manage the unlocking.
        """

        class Lock:
            def __init__(self, tdm, node_id_str):
                self.tdm = tdm
                self.node_id_str = node_id_str
            def __enter__(self):
                return self.node_id_str
            def __exit__(self, type, value, traceback):
                self.tdm.send_unlock_node(node_id_str)

        if node_id_str is None:
            yield from self.wait_for_status(self.NODE_STATUS_AVAILABLE)
            node_id_str = self.first_node()["node_id_str"]
        result = yield from self.lock_node(node_id_str)
        if result is not None:
            raise Exception("Node lock error")
        return Lock(self, node_id_str)

    @types.coroutine
    def compile(self, node_id_str, program, load=True):
        result = yield from self.send_msg_and_get_result(
            lambda notify:
                self.send_program(node_id_str, program, load, request_id_notify=notify)
        )
        return result

    @types.coroutine
    def run(self, node_id_str):
        result = yield from self.send_msg_and_get_result(
            lambda notify:
                self.set_vm_execution_state(node_id_str, self.VM_EXECUTION_STATE_COMMAND_RUN, request_id_notify=notify)
        )
        return result

    @types.coroutine
    def flash(self, node_id_str):
        result = yield from self.send_msg_and_get_result(
            lambda notify:
                self.set_vm_execution_state(node_id_str, self.VM_EXECUTION_STATE_COMMAND_WRITE_PROGRAM_TO_DEVICE_MEMORY, request_id_notify=notify)
        )
        return result

    @types.coroutine
    def watch(self, node_id_str, variables=True, events=True):
        flags = 0x3f # temporary, for tests only
        result = yield from self.send_msg_and_get_result(
            lambda notify:
                self.watch_node(node_id_str, flags, request_id_notify=notify)
        )
        return result

    @staticmethod
    def run_async_program(prog):
        co = prog()
        try:
            while True:
                co.send(None)
        except StopIteration:
            pass
