import getpass
import subprocess
import time
from enum import Enum
from queue import Empty, Queue
from threading import Event, Thread


class PState(Enum):
    STOPPED = 0     # manually stopped
    RUNNING = 1     # currently running
    TERMINATED = 2  # terminated by itself
    FAILED = -1     # stopped, errors occurred


class PController:
    """ A class for controlling third-party applications.

    Controls any command-line program and communicates with it through pipes.
    """

    def __init__(self, cmd=None, args=None, env=None, pipe=True, check_output=False, check_call=False):
        self.cmd = cmd if cmd is not None else ''
        self.args = args
        self.env = env
        self.p = None
        self.pipe = pipe
        self.check_output = check_output
        self.check_call = check_call
        self.start_time = 0
        if self.pipe:
            self.q_stdout = None
            self.q_stderr = None
        self.active = Event()

    def __del__(self):
        if self.p:
            self.stop()

    def run(self):
        """ Run the command in a new process

        Returns:
            PState -- Process status
        """
        self.start_time = time.time()
        if self.check_output:
            # if checking output, return the stdout + stderr
            return subprocess.check_output(self.full_cmd, stderr=subprocess.PIPE, bufsize=1, env=self.env)
        elif self.check_call:
            # if checking output, return the stdout + stderr
            return subprocess.check_call(self.full_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, env=self.env)
        elif self.pipe:
            self.p = subprocess.Popen(self.full_cmd, stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, env=self.env)
            # Queuing output of stdout and stderr
            self.q_stdout = PIORead(self.p.stdout)
            self.q_stderr = PIORead(self.p.stderr)
        else:
            self.p = subprocess.Popen(self.full_cmd, bufsize=0, env=self.env)
        self.active.set()
        return self.pid

    @property
    def pid(self):
        if self.p:
            return self.p.pid
        return None

    def is_running(self):
        if self.p is None:
            return False
        self.p.poll()
        return bool(self.p.returncode is None)

    @property
    def status(self):
        if self.is_running():
            return PState.RUNNING
        self.p.poll()
        if self.p.returncode == 0:
            return PState.TERMINATED
        if self.p.returncode in [-9, -15]:
            return PState.STOPPED
        return PState.FAILED

    def stop(self):
        """ Stops the running process.

        Returns:
            PState -- Process status
        """
        self.active.clear()
        if not self.is_running():
            return self.status
        self.p.terminate()
        term_retries = 5
        while self.is_running() and term_retries > 0:
            self.p.terminate()
            term_retries -= 1
            time.sleep(.1)
        if self.is_running():  # process has not terminated yet
            self.p.kill()
        time.sleep(.1)
        return self.status

    def write(self, message):
        """ Write to the stdin of the controlled process

        Arguments:
            message {str} -- the stdin input for the process
        """
        self.p.stdin.write(message)

    def readline(self, error=False, block=False, decode=True):
        """ Read a line from the output of the controlled process
        Arguments:
            error {bool} -- set to true to get the error output
            block {bool} -- set to true to wait for output, otherwise only get immediately available output

        Returns:
            str -- A line of output of the process
        """
        try:
            line = self.q_stderr.get(
                block) if error else self.q_stdout.get(block)
            if decode:
                return line.strip().decode('utf-8')
            return line
        except Empty:
            return None

    def readAll(self, error=False, decode=False):
        """Reads and returns all output

        Arguments:
            error {bool} -- set to true to get the error output
        Returns:
            list -- A list of lines of output of the process
        """
        lines = []
        while True:
            line = self.readline(error, decode=decode)
            if line:
                lines += [line]
            else:
                break
        return lines

    @property
    def cmd(self):
        """Returns the cmd of the controlled process.
        """
        return self._cmd

    @cmd.setter
    def cmd(self, cmd):
        """Sets the cmd of the controlled process

        Arguments:
            cmd {str} -- the command for the controlled process  
        """
        self._cmd = str(cmd)

    @property
    def args(self):
        """Returns the args of the controlled process.
        """
        return self._args

    @args.setter
    def args(self, args):
        """Sets the args of the controlled process

        Arguments:
            args {[str, list, dict]} -- A dictionary in the form of {'-arg':param}, a list of
                                        seperate arguments, or a one argument string
        """
        self._args = args if isinstance(args, list) else []
        if isinstance(args, dict):
            for k, v in args.items():
                self._args.extend([k, str(v)])
        elif isinstance(args, str):
            self._args = [args]

    def add_args(self, args):
        """Adds args to the existing args list of the controlled process

        Arguments:
            args {[str, list, dict]} -- A dictionary in the form of {'-arg':param}, a list of
                                        seperate arguments, or a one argument string
        """
        if isinstance(args, dict):
            for k, v in args.items():
                self._args.extend([k, str(v)])
        elif isinstance(args, list):
            self._args.extend(args)
        elif isinstance(args, str):
            self._args.append(args)

    @property
    def full_cmd(self):
        """Makes the full command for the controlled process
        """
        self._full_cmd = [self.cmd]
        self._full_cmd.extend(self.args)
        return self._full_cmd

    def __repr__(self):
        return "PController(%s)" % repr(self.full_cmd)


class PIOHandler(Queue):
    """Base class for async subprocess I/O.

    Extends Queue and contains a worker thread to push/pull data from itself to a pipe (or vice versa), asynchronously.
    """

    def __init__(self, pipe, target=None, args=None):
        super().__init__()
        self.pipe = pipe
        if not target:
            self.target = self.process
        self.args = args
        if isinstance(self.args, tuple):
            self.worker = Thread(target=self.target,
                                 args=self.args, daemon=True)
        else:
            self.worker = Thread(target=self.target, daemon=True)
        self.worker.start()

    def process(self):
        raise NotImplementedError(
            "Please derive from PIOHandler and implement the process() method.")


class PIORead(PIOHandler):
    """ Handles asynchronous reading from a subprocess.
    """

    def __init__(self, pipe):
        super().__init__(pipe)

    def process(self):
        """ Reads continually from the pipe and ingests lines into the queue.

        Note: This runs in a separate worker thread.
        """
        for line in iter(self.pipe.readline, b''):
            self.put(line)
        self.pipe.close()


class PIOWrite(PIOHandler):
    """ Handles asynchronous writing to a subprocess.
    """

    def __init__(self, pipe):
        super().__init__(pipe)

    def process(self):
        # TODO: Code that loops around self.get_nowait() and writes the result to self.pipe (reverse of PIORead)
        # Currently not needed (yet).
        pass
