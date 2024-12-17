# pimidipy

`pimidipy` is a Python library developed by [**Blokas**](https://blokas.io/) for Linux ALSA that makes interacting with MIDI devices extremely simple, taking care of all the low-level details for you.

If you're looking to expand your Raspberry Pi's MIDI capabilities, check out [**Pimidi**](https://blokas.io/pimidi/) by Blokas. Pimidi is a hardware add-on that adds 2 MIDI inputs and 2 MIDI outputs to your Raspberry Pi, and it can be stacked up to 4 units high for even more I/O.

Check out the full online documentation of `pimidipy` at https://blokas.io/pimidi/docs/pimidipy/.

## Features

The `pimidipy` library offers:

* A very simple API for working with MIDI data.
* Automatic handling of device disconnects and reconnects.
* Available as a [**Patchbox OS**](https://blokas.io/pimidi/docs/pimidipy-patchbox-module/) module by Blokas for easy auto-run setup.

## A Quick Example

Here's a very short example of how scripting using `pimidipy` would look like. This works seamlessly with **Pimidi** hardware on Raspberry Pi:

```py3
#!/usr/bin/env python3
from pimidipy import *
pimidipy = PimidiPy()

input = pimidipy.open_input('pimidi0:0')   # Pimidi IN A
output = pimidipy.open_output('pimidi0:1') # Pimidi OUT B

def forward(event):
    print(f'Forwarding event {event} from {input.name} to {output.name}')
    output.write(event)

input.add_callback(forward)

pimidipy.run()
```

This is pretty much the base foundation upon which you may build your custom MIDI processing. See the online [API Reference](https://blokas.io/pimidi/docs/pimidipy-reference/) for details on every API.
