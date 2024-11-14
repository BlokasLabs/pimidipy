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
	def __init__(self, handle: PortHandle):
		super().__init__(handle)

	def add_callback(self, callback: Callable[[MIDI_EVENTS], None]):
		self._handle._proc.add_input_callback(self, callback)

	def remove_callback(self, callback: Callable[[MIDI_EVENTS], None]):
		self._handle._proc.remove_input_callback(self, callback)

class OutputPort(PortHandleRef):
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

	def write(self, event: (MIDI_EVENTS | bytearray), drain: bool = True) -> int:
		if isinstance(event, MIDI_EVENTS):
			return self._do_write(partial(self._write_event, event), drain)

		return self._do_write(partial(self._write_data, event), drain)

class PimidiPy:
	_INPUT=0
	_OUTPUT=1

	_input_callbacks: Dict[Tuple[int, int], List[object]]
	_client: alsa_midi.SequencerClient
	_port: alsa_midi.Port
	_open_ports: Array[weakref.WeakValueDictionary[str, PortHandle]]
	_port2name: Array[Dict[Tuple[int, int], Set[str]]]

	def __init__(self, client_name: str = "pimidipy"):
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

	def parse_port_name(self, port_name: str) -> Optional[Tuple[int, int]]:
		addr_p = alsa_midi.ffi.new("snd_seq_addr_t *")
		result = alsa_midi.alsa.snd_seq_parse_address(self._client.handle, addr_p, port_name.encode())
		if result < 0:
			return None
		return addr_p.client, addr_p.port

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
		addr = self.parse_port_name(port)
		if input:
			self._client.unsubscribe_port(addr, self._port)
			self._open_ports[self._INPUT].pop(port)
			self._input_callbacks.pop(port)
		else:
			self._client.unsubscribe_port(self._port, addr)
			self._open_ports[self._OUTPUT].pop(port)

	def open_input(self, port_name: str):
		result = self._open_ports[self._INPUT].get(port_name)

		if result is None:
			result = PortHandle(self, port_name, True)
			self._open_ports[self._INPUT][port_name] = result
			self._input_callbacks[port_name] = []

			port = self.parse_port_name(port_name)
			if port is None:
				stderr.write("Failed to locate Input port by name '{}', will wait for it to appear.\n".format(port_name))
			else:
				self._port2name[self._INPUT][port].add(port_name)
				if not self._subscribe_port(port, self._port):
					stderr.write("Failed to subscribe to Input port '{}'.\n".format(port_name))

		return InputPort(result)

	def open_output(self, port_name: str):
		result = self._open_ports[self._OUTPUT].get(port_name)

		if result is None:
			result = PortHandle(self, port_name, False)
			self._open_ports[self._OUTPUT][port_name] = result

			port = self.parse_port_name(port_name)
			if port is None:
				stderr.write("Failed to locate Output port by name '{}', will wait for it to appear.\n".format(port_name))
			else:
				self._port2name[self._OUTPUT][port].add(port_name)
				if not self._subscribe_port(self._port, port):
					stderr.write("Failed to subscribe to Output port '{}'.\n".format(port_name))
				else:
					result._port = port

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
		self._client.drain_output()

	def quit(self):
		self.done = True

	def run(self):
		self.done = False
		while not self.done:
			try:
				event = self._client.event_input()
				match event.type:
					case alsa_midi.EventType.PORT_START:
						for i in range(2):
							for name, port in self._open_ports[i].items():
								parsed = self.parse_port_name(name)
								if parsed == event.addr:
									if parsed not in self._port2name[i]:
										print("Reopening {} port '{}'".format("Input" if i == self._INPUT else "Output", event.addr))
										if i == self._INPUT:
											self._subscribe_port(parsed, self._port)
										else:
											self._subscribe_port(self._port, parsed)
										port.port = parsed
									print("Adding alias '{}' for {} port '{}'".format(name, "Input" if i == self._INPUT else "Output", event.addr))
									self._port2name[i][parsed].add(name)
					case alsa_midi.EventType.PORT_EXIT:
						for i in range(2):
							for name, port in self._open_ports[i].items():
								parsed = self.parse_port_name(name)
								if parsed == event.addr:
									port.port = None
							if event.addr in self._port2name[i]:
								print("{} port '{}' disappeared.".format("Input" if i == self._INPUT else "Output", event.addr))
								self._port2name[i].pop(event.addr)
					case MIDI_EVENTS:
						port_name_set = self._port2name[self._INPUT].get(event.source, None)
						if port_name_set is not None:
							for port_name in port_name_set:
								if port_name in self._open_ports[self._INPUT] and port_name in self._input_callbacks:
									for callback in self._input_callbacks[port_name]:
										callback(to_pimidipy_event(event))
			except KeyboardInterrupt:
				self.done = True
