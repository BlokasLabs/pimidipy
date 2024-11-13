from collections import defaultdict
from ctypes import Array
from functools import partial
from typing import Dict, List, Optional, Set, Tuple, Callable
from sys import stderr
import weakref
import alsa_midi
import errno

from alsa_midi import (
	NoteOnEvent,
	NoteOffEvent,
	ControlChangeEvent,
	KeyPressureEvent as AftertouchEvent,
	ProgramChangeEvent,
	ChannelPressureEvent,
	PitchBendEvent,
	Control14BitChangeEvent,
	NonRegisteredParameterChangeEvent as NRPNChangeEvent,
	RegisteredParameterChangeEvent as RPNChangeEvent,
	SongPositionPointerEvent,
	SongSelectEvent,
	TimeSignatureEvent,
	KeySignatureEvent,
	StartEvent,
	ContinueEvent,
	StopEvent,
	ClockEvent,
	TuneRequestEvent,
	ResetEvent,
	ActiveSensingEvent,
	SysExEvent,
	MidiBytesEvent
)
from .event_wrappers import to_pimidipy_event

MIDI_EVENTS = (
	NoteOnEvent |
	NoteOffEvent |
	ControlChangeEvent |
	AftertouchEvent |
	ProgramChangeEvent |
	ChannelPressureEvent |
	PitchBendEvent |
	Control14BitChangeEvent |
	NRPNChangeEvent |
	RPNChangeEvent |
	SongPositionPointerEvent |
	SongSelectEvent |
	TimeSignatureEvent |
	KeySignatureEvent |
	StartEvent |
	ContinueEvent |
	StopEvent |
	ClockEvent |
	TuneRequestEvent |
	ResetEvent |
	ActiveSensingEvent |
	SysExEvent |
	MidiBytesEvent
	)

class PortHandle:
	proc: Optional["PimidiPy"]
	port_name: Optional[str]
	port: Optional[alsa_midi.Port]
	input: bool
	refcount: int

	def __init__(self, proc: "PimidiPy", port_name: str, input: bool):
		self.proc = proc
		self.port_name = port_name
		self.port = None
		self.input = input
		self.refcount = 0

	def _sanity_check(self):
		if self.proc is None:
			raise ValueError("The '{}' {} port is closed".format(self.port_name, "Input" if self.input else "Output"))
		
		if self.port is None:
			stderr.write("The '{}' {} port is currently unavailable.\n".format(self.port_name, "Input" if self.input else "Output"))
			return -errno.ENODEV

		return 0

	def addref(self):
		if self.refcount < 0:
			raise ValueError("PortHandle refcount is negative")
		self.refcount += 1

	def close(self):
		if self.refcount >= 1:
			self.refcount -= 1
			return
		elif self.refcount < 0:
			raise ValueError("PortHandle refcount is negative")

		self.proc._unsubscribe_port(self.port_name, self.input)
		self.port_name = None
		self.proc = None

class PortHandleRef:
	_handle: Optional[PortHandle]

	def __init__(self, handle: PortHandle):
		self._handle = handle
		self._handle.addref()

	def __del__(self):
		if self._handle is not None:
			self._handle.close()

	def close(self):
		self._handle.close()
		self._handle = None

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

class InputPort(PortHandleRef):
	def __init__(self, handle: PortHandle):
		super().__init__(handle)

class OutputPort(PortHandleRef):
	def __init__(self, port_handle: PortHandle):
		super().__init__(port_handle)

	def _write_event(self, event: MIDI_EVENTS):
		return self._handle.proc.client.event_output_direct(event, port = self._handle.proc.port, dest = self._handle.port)

	def _write_data(self, data: bytearray):
		return self._handle.proc.client.event_output_direct(MidiBytesEvent(data), port = self._handle.proc.port, dest = self._handle.port)

	def _do_write(self, fn, drain):
		err = self._handle._sanity_check()
		if err < 0:
			return err

		result = fn()

		if drain:
			self._handle.proc.drain_output()

		return result

	def write(self, event: (MIDI_EVENTS | bytearray), drain: bool = True) -> int:
		if isinstance(event, MIDI_EVENTS):
			return self._do_write(partial(self._write_event, event), drain)

		return self._do_write(partial(self._write_data, event), drain)

	def close(self):
		super().close()

class PimidiPy:
	INPUT=0
	OUTPUT=1

	processors: Dict[Tuple[int, int], List[object]]
	client: alsa_midi.SequencerClient
	port: alsa_midi.Port
	open_ports: Array[weakref.WeakValueDictionary[str, PortHandle]]
	port2name: Array[Dict[Tuple[int, int], Set[str]]]

	def __init__(self, client_name: str = "pimidipy"):
		self.processors = {}
		self.open_ports = [weakref.WeakValueDictionary(), weakref.WeakValueDictionary()]
		self.port2name = [defaultdict(set), defaultdict(set)]
		self.client = alsa_midi.SequencerClient(client_name)
		self.port = self.client.create_port(
			client_name,
			caps = alsa_midi.PortCaps.WRITE | alsa_midi.PortCaps.READ | alsa_midi.PortCaps.DUPLEX | alsa_midi.PortCaps.SUBS_READ | alsa_midi.PortCaps.SUBS_WRITE | alsa_midi.PortCaps.NO_EXPORT,
			type = alsa_midi.PortType.MIDI_GENERIC | alsa_midi.PortType.APPLICATION
			)
		self.client.subscribe_port(alsa_midi.SYSTEM_ANNOUNCE, self.port)

	def parse_port_name(self, port_name: str) -> Optional[Tuple[int, int]]:
		addr_p = alsa_midi.ffi.new("snd_seq_addr_t *")
		result = alsa_midi.alsa.snd_seq_parse_address(self.client.handle, addr_p, port_name.encode())
		if result < 0:
			return None
		return addr_p.client, addr_p.port

	def _subscribe_port(self, src, dst):
		try:
			err = self.client.subscribe_port(src, dst)
		except Exception as e:
			err = -1
		if not err is None and err < 0:
			return False
		return True

	def _unsubscribe_port(self, port: str, input: bool):
		print("Unsubscribing {} port '{}'".format("Input" if input else "Output", port))
		addr = self.parse_port_name(port)
		if input:
			self.client.unsubscribe_port(addr, self.port)
			self.open_ports[self.INPUT].pop(port)
			self.processors.pop(port)
		else:
			self.client.unsubscribe_port(self.port, addr)
			self.open_ports[self.OUTPUT].pop(port)

	def open_input(self, port_name: str):
		result = self.open_ports[self.INPUT].get(port_name)

		if result is None:
			result = PortHandle(self, port_name, True)
			self.open_ports[self.INPUT][port_name] = result
			self.processors[port_name] = []

			port = self.parse_port_name(port_name)
			if port is None:
				stderr.write("Failed to locate Input port by name '{}', will wait for it to appear.\n".format(port_name))
			else:
				self.port2name[self.INPUT][port].add(port_name)
				if not self._subscribe_port(port, self.port):
					stderr.write("Failed to subscribe to Input port '{}'.\n".format(port_name))

		return InputPort(result)

	def open_output(self, port_name: str):
		result = self.open_ports[self.OUTPUT].get(port_name)

		if result is None:
			result = PortHandle(self, port_name, False)
			self.open_ports[self.OUTPUT][port_name] = result

			port = self.parse_port_name(port_name)
			if port is None:
				stderr.write("Failed to locate Output port by name '{}', will wait for it to appear.\n".format(port_name))
			else:
				self.port2name[self.OUTPUT][port].add(port_name)
				if not self._subscribe_port(self.port, port):
					stderr.write("Failed to subscribe to Output port '{}'.\n".format(port_name))
				else:
					result.port = port

		return OutputPort(result)

	def register_processor(self, input_port : InputPort, processor : Callable[[alsa_midi.Event], None]):
		if input_port is None or processor is None or input_port._handle is None or input_port._handle.port_name is None:
			raise ValueError("Invalid input_port or processor")

		self.processors[input_port._handle.port_name].append(processor)

	def unregister_processor(self, input_port : InputPort, processor : Callable[[alsa_midi.Event], None]):
		if input_port is None or processor is None or input_port._handle is None or input_port._handle.port_name is None:
			raise ValueError("Invalid input_port or processor")
		self.processors[input_port._handle.port_name].remove(processor)

	def drain_output(self):
		self.client.drain_output()

	def quit(self):
		self.done = True

	def run(self):
		self.done = False
		while not self.done:
			try:
				event = self.client.event_input()
				match event.type:
					case alsa_midi.EventType.PORT_START:
						for i in range(2):
							for name, port in self.open_ports[i].items():
								parsed = self.parse_port_name(name)
								if parsed == event.addr:
									if parsed not in self.port2name[i]:
										print("Reopening {} port '{}'".format("Input" if i == self.INPUT else "Output", event.addr))
										if i == self.INPUT:
											self._subscribe_port(parsed, self.port)
										else:
											self._subscribe_port(self.port, parsed)
										port.port = parsed
									print("Adding alias '{}' for {} port '{}'".format(name, "Input" if i == self.INPUT else "Output", event.addr))
									self.port2name[i][parsed].add(name)
					case alsa_midi.EventType.PORT_EXIT:
						for i in range(2):
							for name, port in self.open_ports[i].items():
								parsed = self.parse_port_name(name)
								if parsed == event.addr:
									port.port = None
							if event.addr in self.port2name[i]:
								print("{} port '{}' disappeared.".format("Input" if i == self.INPUT else "Output", event.addr))
								self.port2name[i].pop(event.addr)
					case MIDI_EVENTS:
						port_name_set = self.port2name[self.INPUT].get(event.source, None)
						if port_name_set is not None:
							for port_name in port_name_set:
								if port_name in self.open_ports[self.INPUT] and port_name in self.processors:
									for processor in self.processors[port_name]:
										processor(to_pimidipy_event(event))
			except KeyboardInterrupt:
				self.done = True
