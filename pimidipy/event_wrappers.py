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

from alsa_midi import (
	NoteOnEvent as NoteOnEventBase,
	NoteOffEvent as NoteOffEventBase,
	ControlChangeEvent as ControlChangeEventBase,
	KeyPressureEvent as AftertouchEventBase,
	ProgramChangeEvent as ProgramChangeEventBase,
	ChannelPressureEvent as ChannelPressureEventBase,
	PitchBendEvent as PitchBendEventBase,
	Control14BitChangeEvent as Control14BitChangeEventBase,
	NonRegisteredParameterChangeEvent as NRPNChangeEventBase,
	RegisteredParameterChangeEvent as RPNChangeEventBase,
	SongPositionPointerEvent as SongPositionPointerEventBase,
	SongSelectEvent as SongSelectEventBase,
	StartEvent as StartEventBase,
	ContinueEvent as ContinueEventBase,
	StopEvent as StopEventBase,
	ClockEvent as ClockEventBase,
	TuneRequestEvent as TuneRequestEventBase,
	ResetEvent as ResetEventBase,
	ActiveSensingEvent as ActiveSensingEventBase,
	SysExEvent as SysExEventBase,
	MidiBytesEvent as MidiBytesEventBase,
	EventType,
)

# Fix up argument ordering to match the rest of the event constructors.
class NoteOnEvent(NoteOnEventBase):
	""" A class representing a Note On event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar note: MIDI Note Number
	:vartype note: int
	:ivar velocity: Note Velocity
	:vartype velocity: int
	"""

	def __init__(self, channel: int, note: int, velocity: int):
		"""
		:param channel: MIDI Channel
		:param note: MIDI Note Number
		:param velocity: Note Velocity
		"""
		super().__init__(channel = channel, note = note, velocity = velocity)

class NoteOffEvent(NoteOffEventBase):
	""" A class representing a Note Off event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar note: MIDI Note Number
	:vartype note: int
	:ivar velocity: Note Velocity
	:vartype velocity: int
	"""
	def __init__(self, channel: int, note: int, velocity: int):
		"""
		:param channel: MIDI Channel
		:param note: MIDI Note Number
		:param velocity: Note Velocity
		"""
		super().__init__(channel = channel, note = note, velocity = velocity)

class ControlChangeEvent(ControlChangeEventBase):
	""" A class representing a Control Change event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar control: Control Number
	:vartype control: int
	:ivar value: Control Value
	:vartype value: int
	"""

	def __init__(self, channel: int, control: int, value: int):
		"""
		:param channel: MIDI Channel
		:param control: Control Number
		:param value: Control Value
		"""
		super().__init__(channel = channel, param = control, value = value)

	@property
	def control(self):
		return self.param

	@control.setter
	def control(self, value):
		self.param = value

class AftertouchEvent(AftertouchEventBase):
	""" A class representing an Aftertouch event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar note: MIDI Note Number
	:vartype note: int
	:ivar value: Aftertouch Value
	:vartype value: int
	"""

	def __init__(self, channel: int, note: int, value: int):
		"""
		:param channel: MIDI Channel
		:param note: MIDI Note Number
		:param value: Aftertouch Value
		"""
		super().__init__(channel = channel, note = note, value = value)

class ProgramChangeEvent(ProgramChangeEventBase):
	""" A class representing a Program Change event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar program: Program Number
	:vartype program: int
	"""

	def __init__(self, channel: int, program: int):
		"""
		:param channel: MIDI Channel
		:param program: Program Number
		"""
		super().__init__(channel = channel, program = program)

class ChannelPressureEvent(ChannelPressureEventBase):
	""" A class representing a Channel Pressure event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar value: Pressure Value
	:vartype value: int
	"""

	def __init__(self, channel: int, value: int):
		"""
		:param channel: MIDI Channel
		:param value: Pressure Value
		"""
		super().__init__(channel = channel, value = value)

class PitchBendEvent(PitchBendEventBase):
	""" A class representing a Pitch Bend event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar value: Pitch Bend Value
	:vartype value: int
	"""

	def __init__(self, channel: int, value: int):
		"""
		:param channel: MIDI Channel
		:param value: Pitch Bend Value
		"""
		super().__init__(channel = channel, value = value)

class Control14BitChangeEvent(Control14BitChangeEventBase):
	""" A class representing a 14-bit Control Change event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar control: Control Number
	:vartype control: int
	:ivar value: Control Value
	:vartype value: int
	"""

	def __init__(self, channel: int, control: int, value: int):
		"""
		:param channel: MIDI Channel
		:param control: Control Number
		:param value: Control Value
		"""
		super().__init__(channel = channel, param = control, value = value)

	@property
	def control(self):
		return self.param

	@control.setter
	def control(self, value):
		self.param = value

class NRPNChangeEvent(NRPNChangeEventBase):
	""" A class representing a Non-Registered Parameter Number Change event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar param: Parameter Number
	:vartype param: int
	:ivar value: Parameter Value
	:vartype value: int
	"""
	def __init__(self, channel: int, param: int, value: int):
		"""
		:param channel: MIDI Channel
		:param param: Parameter Number
		:param value: Parameter Value
		"""
		super().__init__(channel = channel, param = param, value = value)

class RPNChangeEvent(RPNChangeEventBase):
	""" A class representing a Registered Parameter Number Change event.

	:ivar channel: MIDI Channel
	:vartype channel: int
	:ivar param: Parameter Number
	:vartype param: int
	:ivar value: Parameter Value
	:vartype value: int
	"""
	def __init__(self, channel: int, param: int, value: int):
		"""
		:param channel: MIDI Channel
		:param param: Parameter Number
		:param value: Parameter Value
		"""
		super().__init__(channel = channel, param = param, value = value)

class SongPositionPointerEvent(SongPositionPointerEventBase):
	""" A class representing a Song Position Pointer event.

	:ivar position: Song Position - 14-bit value. Position is counted in "MIDI beats" (1 beat = 6 MIDI clocks)
	:vartype position: int
	"""
	def __init__(self, position: int):
		"""
		:param position: Song Position
		"""
		super().__init__(position = position)

class SongSelectEvent(SongSelectEventBase):
	""" A class representing a Song Select event.

	:ivar song: Song Number
	:vartype song: int
	"""

	def __init__(self, song: int):
		"""
		:param song: Song Number
		"""
		super().__init__(song = song)

class StartEvent(StartEventBase):
	""" A class representing a Start event. """
	def __init__(self):
		""" Default Constructor. """
		super().__init__()

class ContinueEvent(ContinueEventBase):
	""" A class representing a Continue event. """
	def __init__(self):
		""" Default Constructor. """
		super().__init__()

class StopEvent(StopEventBase):
	""" A class representing a Stop event. """
	def __init__(self):
		""" Default Constructor. """
		super().__init__()

class ClockEvent(ClockEventBase):
	""" A class representing a Clock event. 24 Clock events make up a quarter note. """
	def __init__(self):
		""" Default Constructor. """
		super().__init__()

class TuneRequestEvent(TuneRequestEventBase):
	""" A class representing a Tune Request event. """
	def __init__(self):
		""" Default Constructor. """
		super().__init__()

class ResetEvent(ResetEventBase):
	""" A class representing a Reset event. """
	def __init__(self):
		""" Default Constructor. """
		super().__init__()

class ActiveSensingEvent(ActiveSensingEventBase):
	""" A class representing an Active Sensing event. """
	def __init__(self):
		""" Default Constructor. """
		super().__init__()

class SysExEvent(SysExEventBase):
	""" A class representing a System Exclusive event.

	:ivar data: SysEx Data
	:vartype data: bytes
	"""

	def __init__(self, data: bytes):
		"""
		:param data: SysEx Data
		"""
		super().__init__(data = data)

class MidiBytesEvent(MidiBytesEventBase):
	""" A class for writing Raw MIDI Bytes to an OutputPort.

	:ivar data: Raw MIDI Bytes
	:vartype data: bytes
	"""

	def __init__(self, data: bytes):
		"""
		:param data: Raw MIDI Bytes
		"""
		super().__init__(data = data)

mappings = {
	NoteOnEventBase: lambda x: NoteOnEvent(x.channel, x.note, x.velocity),
	NoteOffEventBase: lambda x: NoteOffEvent(x.channel, x.note, x.velocity),
	ControlChangeEventBase: lambda x: ControlChangeEvent(x.channel, x.param, x.value),
	AftertouchEventBase: lambda x: AftertouchEvent(x.channel, x.note, x.value),
	ProgramChangeEventBase: lambda x: ProgramChangeEvent(x.channel, x.program),
	ChannelPressureEventBase: lambda x: ChannelPressureEvent(x.channel, x.value),
	PitchBendEventBase: lambda x: PitchBendEvent(x.channel, x.value),
	Control14BitChangeEventBase: lambda x: Control14BitChangeEvent(x.channel, x.control, x.value),
	NRPNChangeEventBase: lambda x: NRPNChangeEvent(x.channel, x.param, x.value),
	RPNChangeEventBase: lambda x: RPNChangeEvent(x.channel, x.param, x.value),
	SongPositionPointerEventBase: lambda x: SongPositionPointerEvent(x.position),
	SongSelectEventBase: lambda x: SongSelectEvent(x.song),
	StartEventBase: lambda x: StartEvent(),
	ContinueEventBase: lambda x: ContinueEvent(),
	StopEventBase: lambda x: StopEvent(),
	ClockEventBase: lambda x: ClockEvent(),
	TuneRequestEventBase: lambda x: TuneRequestEvent(),
	ResetEventBase: lambda x: ResetEvent(),
	ActiveSensingEventBase: lambda x: ActiveSensingEvent(),
	SysExEventBase: lambda x: SysExEvent(x.data),
	MidiBytesEventBase: lambda x: MidiBytesEvent(x.data),
}

def to_pimidipy_event(alsa_event):
	return mappings.get(type(alsa_event), lambda x: x)(alsa_event)
