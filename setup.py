#!/usr/bin/env python36

from setuptools import setup

setup(
	name = 'seafileUploader',
	version = '1.0',

	author = 'Matthew Pogue, Dominic Canare',
	author_email = 'matthewpogue606@gmail.com',

	description = 'A package used to upload files to a seafile server',
	long_description = open('README.md').read(),

	url = 'https://git.vpclab.com/VPCLab/seafileUploader',
	packages = setuptools.find_packages(),
)

