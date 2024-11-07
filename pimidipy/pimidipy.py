from typing import Dict, List, Optional, Tuple, Callable
from sys import stderr
import weakref
import alsa_midi

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
	SysExEvent
)

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
	SysExEvent
	)

class PortHandle:
	proc: Optional["PimidiPy"]
	port_name: Optional[str]
	input: bool

	def __init__(self, proc: "PimidiPy", port_name: str, input: bool):
		self.proc = proc
		self.port_name = port_name
		self.input = input

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()
		return False

	def close(self):
		print("PortHandle.close {}".format(self.proc))
		if self.proc is None:
			return
		self.proc._unsubscribe_port(self.port_name, self.input)
		self.port_name = None
		self.proc = None

class InputPort(PortHandle):
	def __init__(self, proc: "PimidiPy", port_name: str):
		super().__init__(proc, port_name, True)

	#def __del__(self):
	#	print("InputPort.__del__")
	#	del self.proc.open_inputs[self.port]
	#	#self.proc.open_inputs.pop(self.port)
	#	if self.port in self.proc.processors:
	#		del self.proc.processors[self.port]
	#	super().__del__()

class OutputPort(PortHandle):
	port : Optional[alsa_midi.Port]

	def __init__(self, proc: "PimidiPy", port_name: str):
		super().__init__(proc, port_name, False)

	#def __del__(self):
	#	print("OutputPort.__del__")
	#	del self.proc.open_outputs[self.port]
	#	super().__del__()

	def write(self, event: MIDI_EVENTS, drain: bool = True):
		if self.proc is None:
			raise ValueError("OutputPort is closed")

		if self.port is None:
			stderr.write("OutputPort.write: The port is currently unavailable.\n")
			return

		self.proc.client.event_output_direct(event, port = self.proc.port, dest = self.port)
		if drain:
			self.proc.drain_output()

	def close(self):
		super().close()
		self.port = None

class PimidiPy:
	processors: Dict[Tuple[int, int], List[object]]
	client: alsa_midi.SequencerClient
	port: alsa_midi.Port
	open_inputs: weakref.WeakValueDictionary[str, InputPort]
	open_outputs: weakref.WeakValueDictionary[str, OutputPort]
	port2name: Dict[Tuple[int, int], str]

	def __init__(self):
		self.processors = {}
		self.open_inputs = weakref.WeakValueDictionary()
		self.open_outputs = weakref.WeakValueDictionary()
		self.port2name = {}
		self.client = alsa_midi.SequencerClient("pymidiproc")
		self.port = self.client.create_port(
			"pymidiproc",
			caps = alsa_midi.PortCaps.WRITE | alsa_midi.PortCaps.READ | alsa_midi.PortCaps.DUPLEX | alsa_midi.PortCaps.SUBS_READ | alsa_midi.PortCaps.SUBS_WRITE | alsa_midi.PortCaps.NO_EXPORT,
			type = alsa_midi.PortType.MIDI_GENERIC | alsa_midi.PortType.APPLICATION
			)
		self.client.subscribe_port(alsa_midi.SYSTEM_ANNOUNCE, self.port)

	def __del__(self):
		print("PymidiProc.__del__")

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
		print("Unsubscribing port {}".format(port))
		addr = self.parse_port_name(port)
		if input:
			self.client.unsubscribe_port(addr, self.port)
			self.open_inputs.pop(port)
			self.processors.pop(port)
		else:
			self.client.unsubscribe_port(self.port, addr)
			self.open_outputs.pop(port)

	def open_input(self, port_name: str):
		result = self.open_inputs.get(port_name)

		if result is None:
			result = InputPort(self, port_name)
			self.open_inputs[port_name] = result
			self.processors[port_name] = []

			port = self.parse_port_name(port_name)
			if port is None:
				stderr.write("Failed to locate Input port by name '{}', will wait for it to appear.\n".format(port_name))
			else:
				self.port2name[port] = port_name
				if not self._subscribe_port(port, self.port):
					stderr.write("Failed to subscribe to Input port '{}'.\n".format(port_name))

		print("open_input: {} {}".format(port, self.open_inputs[port_name]))
		return result

	def open_output(self, port_name: str):
		result = self.open_outputs.get(port_name)

		if result is None:
			result = OutputPort(self, port_name)
			self.open_outputs[port_name] = result

			port = self.parse_port_name(port_name)
			if port is None:
				stderr.write("Failed to locate Output port by name '{}', will wait for it to appear.\n".format(port_name))
			else:
				self.port2name[port] = port_name
				if not self._subscribe_port(self.port, port):
					stderr.write("Failed to subscribe to Output port '{}'.\n".format(port_name))
				else:
					result.port = port

		return result

	def register_processor(self, input_port : InputPort, processor : Callable[[alsa_midi.Event], None]):
		if input_port is None or processor is None:
			raise ValueError("input_port and processor must not be None")

		self.processors[input_port.port_name].append(processor)

	def unregister_processor(self, input_port : InputPort, processor : Callable[[alsa_midi.Event], None]):
		if input_port is None or processor is None:
			raise ValueError("input_port and processor must not be None")
		self.processors[input_port].remove(processor)

	def drain_output(self):
		self.client.drain_output()

	def quit(self):
		self.done = True

	def run(self):
		print("Hello from pymidiproc!")
		print(self.client._fd)
		self.done = False
		while not self.done:
			try:
				event = self.client.event_input()
				match event.type:
					case alsa_midi.EventType.PORT_START:
						for name, port in self.open_inputs.items():
							parsed = self.parse_port_name(name)
							if parsed == event.addr:
								print("Reopening input_port {}".format(event.addr))
								self._subscribe_port(parsed, self.port)
								self.port2name[parsed] = name
						for name, port in self.open_outputs.items():
							parsed = self.parse_port_name(name)
							if parsed == event.addr:
								print("Reopening output_port {}".format(event.addr))
								self._subscribe_port(self.port, parsed)
								self.port2name[parsed] = name
								port.port = parsed
					case alsa_midi.EventType.PORT_EXIT:
						self.port2name.pop(event.addr)
					case MIDI_EVENTS:
						port_name = self.port2name.get(event.source, None)
						if port_name is not None and port_name in self.open_inputs and port_name in self.processors:
							for processor in self.processors[port_name]:
								processor(event)
				#print(repr(event))
			except KeyboardInterrupt:
				self.done = True
