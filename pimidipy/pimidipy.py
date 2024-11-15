# pimidipy
# Copyright (C) 2024  UAB Vilniaus blokas
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see https://www.gnu.org/licenses/.

from collections import defaultdict
from ctypes import Array
from functools import partial
from typing import Dict, List, Optional, Set, Tuple, Callable, Union
from sys import stderr
from enum import IntFlag
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
from .type_wrappers import to_pimidipy_event

MIDI_EVENTS = Union[
	NoteOnEvent,
	NoteOffEvent,
	ControlChangeEvent,
	AftertouchEvent,
	ProgramChangeEvent,
	ChannelPressureEvent,
	PitchBendEvent,
	Control14BitChangeEvent,
	NRPNChangeEvent,
	RPNChangeEvent,
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
]

class PortDirection(IntFlag):
	""" PortDirection is an enumeration of MIDI port directions.
	
	Available values are:

	- `ANY`: Any direction. Useful for use with [`PimidiPy.list_ports`][pimidipy.PimidiPy.list_ports]
	- `INPUT`: Input port.
	- `OUTPUT`: Output port.
	- `BOTH`: Input and output port.

	The values can be used as bitwise flags.
	"""
	ANY    = 0
	INPUT  = 1 << 0
	OUTPUT = 1 << 1
	BOTH   = INPUT | OUTPUT

class PortInfo:
	""" PortInfo class, which is returned by [`PimidiPy.list_ports`][pimidipy.PimidiPy.list_ports],
	holds a collection of MIDI port attributes.

	:ivar client_name: The name of the client owning the port.
	:vartype client_name: str
	:ivar port_name: The name of the port.
	:vartype port_name: str
	:ivar client_id: The client ID.
	:vartype client_id: int
	:ivar port_id: The port ID.
	:vartype port_id: int
	:ivar address: The address of the port in the form of 'client_id:port_id'.
	:vartype address: str
	:ivar direction: The direction of the port.
	:vartype direction: PortDirection
	:ivar capabilities: The capabilities of the port. See [SND_SEQ_PORT_CAP_...](https://www.alsa-project.org/alsa-doc/alsa-lib/group___seq_port.html){:target="_blank"} enum docs for more information.
	:vartype capabilities: PortCaps
	:ivar type: The type of the port. See [SND_SEQ_PORT_TYPE_...](https://www.alsa-project.org/alsa-doc/alsa-lib/group___seq_port.html){:target="_blank"} enum docs for more information.
	:vartype type: PortType
	"""
	client_name: str
	port_name: str
	client_id: int
	port_id: int
	address: str
	direction: PortDirection
	capabilities: alsa_midi.PortCaps
	type: alsa_midi.PortType

	def __init__(self, client_name: str, port_name: str, client_id: int, port_id: int, address: str, direction: PortDirection, capabilities: alsa_midi.PortCaps, type: alsa_midi.PortType):
		self.client_name = client_name
		self.port_name = port_name
		self.client_id = client_id
		self.port_id = port_id
		self.address = address
		self.direction = direction
		self.capabilities = capabilities
		self.type = type

	def __repr__(self):
		return f"PortInfo(client_name='{self.client_name}', port_name='{self.port_name}', address='{self.address}', direction={self.direction}, capabilities={self.capabilities}, type={self.type})"

class PortHandle:
	_proc: Optional["PimidiPy"]
	_port_name: Optional[str]
	_port: Optional[alsa_midi.Port]
	_input: bool
	_refcount: int

	def __init__(self, proc: "PimidiPy", port_name: str, input: bool):
		self._proc = proc
		self._port_name = port_name
		self._port = None
		self._input = input
		self._refcount = 0

	def _sanity_check(self):
		if self._proc is None:
			raise ValueError("The '{}' {} port is closed".format(self._port_name, "Input" if self._input else "Output"))
		
		if self._port is None:
			stderr.write("The '{}' {} port is currently unavailable.\n".format(self._port_name, "Input" if self._input else "Output"))
			return -errno.ENODEV

		return 0

	def _addref(self):
		if self._refcount < 0:
			raise ValueError("PortHandle refcount is negative")
		self._refcount += 1

	def close(self):
		if self._refcount >= 1:
			self._refcount -= 1
			return
		elif self._refcount < 0:
			raise ValueError("PortHandle refcount is negative")

		self._proc._unsubscribe_port(self._port_name, self._input)
		self._port_name = None
		self._proc = None

class PortHandleRef:
	_handle: Optional[PortHandle]

	def __init__(self, handle: PortHandle):
		self._handle = handle
		self._handle._addref()

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
	""" InputPort class represents a MIDI input port. """
	def __init__(self, handle: PortHandle):
		super().__init__(handle)

	def add_callback(self, callback: Callable[[MIDI_EVENTS], None]):
		""" Add a callback function to be called when a MIDI event is received from the input port.

		:param callback: The callback function to add.
		"""
		self._handle._proc.add_input_callback(self, callback)

	def remove_callback(self, callback: Callable[[MIDI_EVENTS], None]):
		""" Remove a previously added callback function from the input port.

		:param callback: The callback function to remove.
		"""
		self._handle._proc.remove_input_callback(self, callback)

	def close(self):
		""" Optional function to close the input port.

		Note that if there's multiple InputPort instances referring to the same port,
		the port will only be closed when all of them are closed.
		"""
		super().close()

class OutputPort(PortHandleRef):
	""" OutputPort class represents a MIDI output port. """
	def __init__(self, port_handle: PortHandle):
		super().__init__(port_handle)

	def _write_event(self, event: MIDI_EVENTS):
		return self._handle._proc._client.event_output_direct(event, port = self._handle._proc._port, dest = self._handle._port)

	def _write_data(self, data: bytearray):
		return self._handle._proc._client.event_output_direct(MidiBytesEvent(data), port = self._handle._proc._port, dest = self._handle._port)

	def _do_write(self, fn, drain):
		err = self._handle._sanity_check()
		if err < 0:
			return err

		result = fn()

		if drain:
			self._handle._proc.drain_output()

		return result

	def write(self, event: Union[MIDI_EVENTS, bytearray], drain: bool = True) -> int:
		"""Write a MIDI event or raw data to the output port.

		The function accepts either one of the Event classes defined below, or raw MIDI data
		in the form of a bytearray.

		:param event: The MIDI event or raw data to write.
		:param drain: If `True`, the output buffer will be drained after writing the event.
		:return: The number of bytes written, or a negative error code.
		:rtype: int
		"""
		if isinstance(event, MIDI_EVENTS):
			return self._do_write(partial(self._write_event, event), drain)

		return self._do_write(partial(self._write_data, event), drain)

	def close(self):
		""" Optional function to close the output port.

		Note that if there's multiple OutputPort instances referring to the same port,
		the port will only be closed when all of them are closed.
		"""
		super().close()

class PimidiPy:
	""" PimidiPy class is the main gateway to the `pimidipy` library.

	PimidiPy provides functions to open and close MIDI ports as well as to run the main loop.
	"""
	_INPUT=0
	_OUTPUT=1

	_input_callbacks: Dict[Tuple[int, int], List[object]]
	_client: alsa_midi.SequencerClient
	_port: alsa_midi.Port
	_open_ports: Array[weakref.WeakValueDictionary[str, PortHandle]]
	_port2name: Array[Dict[Tuple[int, int], Set[str]]]

	def __init__(self, client_name: str = "pimidipy"):
		""" Initialize the PimidiPy object.

		:param client_name: The name of the ALSA Sequencer client to create.
		"""
		self._input_callbacks = {}
		self._open_ports = [weakref.WeakValueDictionary(), weakref.WeakValueDictionary()]
		self._port2name = [defaultdict(set), defaultdict(set)]
		self._client = alsa_midi.SequencerClient(client_name)
		self._port = self._client.create_port(
			client_name,
			caps = alsa_midi.PortCaps.WRITE | alsa_midi.PortCaps.READ | alsa_midi.PortCaps.DUPLEX | alsa_midi.PortCaps.SUBS_READ | alsa_midi.PortCaps.SUBS_WRITE | alsa_midi.PortCaps.NO_EXPORT,
			type = alsa_midi.PortType.MIDI_GENERIC | alsa_midi.PortType.APPLICATION
			)
		self._client.subscribe_port(alsa_midi.SYSTEM_ANNOUNCE, self._port)

	def list_ports(self, direction: PortDirection = PortDirection.ANY) -> List[PortInfo]:
		""" List all available MIDI ports.

		:return: A list of `PortInfo` objects.
		"""

		input = False
		output = False

		if direction == PortDirection.ANY:
			input = None
			output = None
		else:
			input = direction & PortDirection.INPUT
			output = direction & PortDirection.OUTPUT

		ports = self._client.list_ports(
			input = input,
			output = output,
			include_no_export=False,
			only_connectable=True
			)

		result = []

		for port in ports:
			result.append(PortInfo(
				client_name = port.client_name,
				port_name = port.name,
				client_id = port.client_id,
				port_id = port.port_id,
				address = f"{port.client_id}:{port.port_id}",
				direction = (PortDirection.INPUT if port.capability & alsa_midi.PortCaps.READ else 0) | (PortDirection.OUTPUT if port.capability & alsa_midi.PortCaps.WRITE else 0),
				capabilities = port.capability,
				type = port.type
			))

		return result

	def _parse_port_name(self, port_name: str) -> Optional[Tuple[int, int]]:
		addr_p = alsa_midi.ffi.new("snd_seq_addr_t *")
		result = alsa_midi.alsa.snd_seq_parse_address(self._client.handle, addr_p, port_name.encode())
		if result < 0:
			return None
		return addr_p.client, addr_p.port

	def resolve_port_name(self, port_name: str) -> Optional[str]:
		"""Utility to resolve an ALSA Sequencer MIDI port name into a 'client_id:port_id' string.

		:param port_name: The name of the port to parse.
		:return: A normalized 'client_id:port_id' string, or None if the port was not found.
		"""

		addr_p = self._parse_port_name(port_name)
		return "{}:{}".format(addr_p.client, addr_p.port)

	def _subscribe_port(self, src, dst):
		try:
			err = self._client.subscribe_port(src, dst)
		except Exception as e:
			err = -1
		if not err is None and err < 0:
			return False
		return True

	def _unsubscribe_port(self, port: str, input: bool):
		print("Unsubscribing {} port '{}'".format("Input" if input else "Output", port))
		addr = self._parse_port_name(port)
		if input:
			self._client.unsubscribe_port(addr, self._port)
			self._open_ports[self._INPUT].pop(port)
			self._input_callbacks.pop(port)
		else:
			self._client.unsubscribe_port(self._port, addr)
			self._open_ports[self._OUTPUT].pop(port)

	def open_input(self, port: Union[str, PortInfo, Tuple[int, int]]) -> InputPort:
		"""Open an input port by name.

		In case the port is not currently available, an `InputPort` object is still
		returned, and it will subscribe to the appropriate device as soon as it is
		connected automatically.

		:param port: The name/info/address of the port to open.
		:return: An InputPort object representing the opened port.
		:rtype: InputPort
		"""

		if isinstance(port, PortInfo):
			port = f"{port.client_name}:{port.port_id}"
		elif isinstance(port, tuple):
			port = f"{port[0]}:{port[1]}"

		result = self._open_ports[self._INPUT].get(port)

		if result is None:
			result = PortHandle(self, port, True)
			self._open_ports[self._INPUT][port] = result
			self._input_callbacks[port] = []

			p = self._parse_port_name(port)
			if p is None:
				stderr.write("Failed to locate Input port by name '{}', will wait for it to appear.\n".format(port))
			else:
				self._port2name[self._INPUT][p].add(port)
				if not self._subscribe_port(p, self._port):
					stderr.write("Failed to subscribe to Input port '{}'.\n".format(port))

		return InputPort(result)

	def open_output(self, port: Union[str, PortInfo, Tuple[int, int]]) -> OutputPort:
		"""Open an output port by name.

		In case the port is not currently available, an OutputPort object is still
		returned, and it will subscribe to the appropriate device as soon as it is
		connected automatically.

		:param port: The name/address/info of the port to open.
		:return: An OutputPort object representing the opened port.
		:rtype: OutputPort
		"""

		if isinstance(port, PortInfo):
			port = f"{port.client_name}:{port.port_id}"
		elif isinstance(port, tuple):
			port = f"{port[0]}:{port[1]}"

		result = self._open_ports[self._OUTPUT].get(port)

		if result is None:
			result = PortHandle(self, port, False)
			self._open_ports[self._OUTPUT][port] = result

			p = self._parse_port_name(port)
			if p is None:
				stderr.write("Failed to locate Output port by name '{}', will wait for it to appear.\n".format(port))
			else:
				self._port2name[self._OUTPUT][p].add(port)
				if not self._subscribe_port(self._port, p):
					stderr.write("Failed to subscribe to Output port '{}'.\n".format(port))
				else:
					result._port = p

		return OutputPort(result)

	def add_input_callback(self, input_port : InputPort, callback : Callable[[MIDI_EVENTS], None]):
		if input_port is None or callback is None or input_port._handle is None or input_port._handle._port_name is None:
			raise ValueError("Invalid input_port or callback")

		self._input_callbacks[input_port._handle._port_name].append(callback)

	def remove_input_callback(self, input_port : InputPort, callback : Callable[[MIDI_EVENTS], None]):
		if input_port is None or callback is None or input_port._handle is None or input_port._handle._port_name is None:
			raise ValueError("Invalid input_port or callback")
		self._input_callbacks[input_port._handle._port_name].remove(callback)

	def drain_output(self):
		""" Drain the output buffer. Use this when if you set `drain` to `False` in [`OutputPort.write`][pimidipy.OutputPort.write]."""
		self._client.drain_output()

	def quit(self):
		""" Ask the main loop to stop. """
		self.done = True

	def run(self):
		""" Run the main loop. """
		self.done = False
		while not self.done:
			try:
				event = self._client.event_input()
				if isinstance(event, MIDI_EVENTS):
					port_name_set = self._port2name[self._INPUT].get(event.source, None)
					if port_name_set is not None:
						for port_name in port_name_set:
							if port_name in self._open_ports[self._INPUT] and port_name in self._input_callbacks:
								for callback in self._input_callbacks[port_name]:
									callback(to_pimidipy_event(event))
				elif event.type == alsa_midi.EventType.PORT_START:
					for i in range(2):
						for name, port in self._open_ports[i].items():
							parsed = self._parse_port_name(name)
							if parsed == event.addr:
								if parsed not in self._port2name[i]:
									print("Reopening {} port '{}'".format("Input" if i == self._INPUT else "Output", event.addr))
									if i == self._INPUT:
										self._subscribe_port(parsed, self._port)
									else:
										self._subscribe_port(self._port, parsed)
									port._port = parsed
								print("Adding alias '{}' for {} port '{}'".format(name, "Input" if i == self._INPUT else "Output", event.addr))
								self._port2name[i][parsed].add(name)
				elif event.type == alsa_midi.EventType.PORT_EXIT:
					for i in range(2):
						for name, port in self._open_ports[i].items():
							parsed = self._parse_port_name(name)
							if parsed == event.addr:
								port._port = None
						if event.addr in self._port2name[i]:
							print("{} port '{}' disappeared.".format("Input" if i == self._INPUT else "Output", event.addr))
							self._port2name[i].pop(event.addr)
			except KeyboardInterrupt:
				self.done = True
