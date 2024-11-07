from .pimidipy import PimidiPy, InputPort, OutputPort
from alsa_midi import (
	NoteOnEvent as NoteOnEventBase,
	NoteOffEvent as NoteOffEventBase,
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

# Fix up argument ordering to match the rest of the event constructors.
class NoteOnEvent(NoteOnEventBase):
	def __init__(self, channel: int, note: int, velocity: int):
		super().__init__(channel = channel, note = note, velocity = velocity)

class NoteOffEvent(NoteOffEventBase):
	def __init__(self, channel: int, note: int, velocity: int):
		super().__init__(channel = channel, note = note, velocity = velocity)
