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

from setuptools import find_packages, setup

setup(
	name='pimidipy',
	packages=find_packages(include=['pimidipy']),
	version='0.1.0',
	description='pimidipy MIDI processing library',
	author='Blokas',
	requires='alsa_midi'
)
