# pimidipy

`pimidipy` is a Python library developed by [**Blokas**](https://blokas.io/) for Linux ALSA that makes interacting with MIDI devices extremely simple, taking care of all the low-level details for you.

Check out the full online documentation of `pimidipy` at https://blokas.io/pimidi/docs/pimidipy/.

If you're looking to expand your Raspberry Pi's MIDI capabilities, check out [**Pimidi**](https://blokas.io/pimidi/) HAT by Blokas. Pimidi is a hardware add-on that adds 2 MIDI inputs and 2 MIDI outputs to your Raspberry Pi, and it can be stacked up to 4 units high for even more MIDI I/O.

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

## Contributing

We warmly invite the open-source community to help us improve and extend the `pimidipy` library. Whether you want to add new features, fix bugs, or improve documentation, we welcome your contributions!

### Getting Started
1. **Install prerequisites** (if not already installed):
   Make sure `pip` for Python 3 is available on your system. You can install it using:
   ```bash
   sudo apt update
   sudo apt install python3-pip
   ```

2. **Fork** the repository and clone it to your local machine:
   ```bash
   git clone https://github.com/your-username/pimidipy.git
   cd pimidipy
   ```

3. **Install the library locally** in editable mode using `pip`:
   ```bash
   pip3 install --break-system-packages -e .
   ```

   This allows you to make changes to the library and test them immediately without needing to reinstall it.

4. **Make your changes** and test them locally.

5. **Submit your changes** as a pull request.

6. Join the conversation in our [community forums](https://community.blokas.io/c/pimidi/26) to discuss ideas, get support, or share your projects.

Your contributions will help make `pimidipy` even better for everyone. Thank you for being part of the Blokas community!
