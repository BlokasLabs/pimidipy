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
	TimeSignatureEvent as TimeSignatureEventBase,
	KeySignatureEvent as KeySignatureEventBase,
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
	def __init__(self, channel: int, note: int, velocity: int):
		super().__init__(channel = channel, note = note, velocity = velocity)

class NoteOffEvent(NoteOffEventBase):
	def __init__(self, channel: int, note: int, velocity: int):
		super().__init__(channel = channel, note = note, velocity = velocity)

class ControlChangeEvent(ControlChangeEventBase):
	def __init__(self, channel: int, control: int, value: int):
		super().__init__(channel = channel, param = control, value = value)

	@property
	def control(self):
		return self.param

	@control.setter
	def control(self, value):
		self.param = value

class AftertouchEvent(AftertouchEventBase):
	def __init__(self, channel: int, note: int, value: int):
		super().__init__(channel = channel, note = note, value = value)

class ProgramChangeEvent(ProgramChangeEventBase):
	def __init__(self, channel: int, program: int):
		super().__init__(channel = channel, program = program)

class ChannelPressureEvent(ChannelPressureEventBase):
	def __init__(self, channel: int, value: int):
		super().__init__(channel = channel, value = value)

class PitchBendEvent(PitchBendEventBase):
	def __init__(self, channel: int, value: int):
		super().__init__(channel = channel, value = value)

class Control14BitChangeEvent(Control14BitChangeEventBase):
	def __init__(self, channel: int, control: int, value: int):
		super().__init__(channel = channel, control = control, value = value)

class NRPNChangeEvent(NRPNChangeEventBase):
	def __init__(self, channel: int, param: int, value: int):
		super().__init__(channel = channel, param = param, value = value)

class RPNChangeEvent(RPNChangeEventBase):
	def __init__(self, channel: int, param: int, value: int):
		super().__init__(channel = channel, param = param, value = value)

class SongPositionPointerEvent(SongPositionPointerEventBase):
	def __init__(self, position: int):
		super().__init__(position = position)

class SongSelectEvent(SongSelectEventBase):
	def __init__(self, song: int):
		super().__init__(song = song)

class TimeSignatureEvent(TimeSignatureEventBase):
	def __init__(self, numerator: int, denominator: int, metronome: int, thirtyseconds: int):
		super().__init__(numerator = numerator, denominator = denominator, metronome = metronome, thirtyseconds = thirtyseconds)

class KeySignatureEvent(KeySignatureEventBase):
	def __init__(self, key: int, scale: int):
		super().__init__(key = key, scale = scale)

class StartEvent(StartEventBase):
	pass

class ContinueEvent(ContinueEventBase):
	pass

class StopEvent(StopEventBase):
	pass

class ClockEvent(ClockEventBase):
	pass

class TuneRequestEvent(TuneRequestEventBase):
	pass

class ResetEvent(ResetEventBase):
	pass

class ActiveSensingEvent(ActiveSensingEventBase):
	pass

class SysExEvent(SysExEventBase):
	def __init__(self, data: bytes):
		super().__init__(data = data)

class MidiBytesEvent(MidiBytesEventBase):
	def __init__(self, data: bytes):
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
	TimeSignatureEventBase: lambda x: TimeSignatureEvent(x.numerator, x.denominator, x.metronome, x.thirtyseconds),
	KeySignatureEventBase: lambda x: KeySignatureEvent(x.key, x.scale),
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
