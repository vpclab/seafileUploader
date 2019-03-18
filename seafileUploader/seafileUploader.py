#!/usr/bin/env python36

import os
import glob
import requests
import platform
import logging
import shutil

from PySide2 import QtCore

import configparser

class UploadThread(QtCore.QThread):
	progress = QtCore.Signal(float)
	status = QtCore.Signal(str)
	complete = QtCore.Signal()
	error = QtCore.Signal(object)

	def __init__(self, local_path, remote_path, repo_id, username, password, resting_path='uploaded'):
		# QThread constructor
		super().__init__()

		# Constructor to member variables
		self.repoID = repo_id
		self.username = username
		self.password = password
		self.localPath = local_path
		self.remotePath = remote_path
		self.restingPath = resting_path

		# Creating an empty token
		self.token = None

		# Setting the upload path
		self.uploadPath = '/' + remote_path

	def generateAuthToken(self):
		''' Sets self.token with a valid authorization for the given repo and login.'''
		# Updating status
		self.status.emit('Getting authorization token...')

		# Removing current token if exists
		self.token = None

		# Requesting token from VPCLab's drive
		authRequest = requests.post(
			'https://drive.vpclab.com/api2/auth-token/',
			data={
				'username': self.username,
				'password': self.password,
			}
		)

		# Setting the token if we get it as a request
		try:
			authResponse = authRequest.json()
			if 'token' in authResponse:
				self.token = authResponse['token']
		except Exception as exc:
			# There was an exception, we stopping
			print(exc)
			raise Exception('Authentication failed')

	def getUploadLink(self, path):
		# Updating current status
		self.status.emit('Getting upload link...')

		# Returning the new upload link
		return requests.get(
			f'https://drive.vpclab.com/api2/repos/{self.repoID}/upload-link/?p=/{path}',
			headers={'Authorization': f'Token {self.token}'},
		)

	def makeRemoteDirectory(self, path):
		# Updating current status
		self.status.emit(f'Creating remote directory `{path}`...')

		# Posting request for new directory
		mkdirRequest = requests.post(
			f'https://drive.vpclab.com/api2/repos/{self.repoID}/dir/?p=/{path}',
			data={'operation': 'mkdir'},
			headers={'Authorization': f'Token {self.token}'},
		)

		# Checking the folder creating request
		mkdirRequest.raise_for_status()

	def _discoverLocalFiles(self):
		# Updating status
		self.status.emit('Discovering local files...')

		# Getting the files in the local path given
		files = glob.glob(os.path.join(self.localPath, '*'))

		# Filtering out directories before uploading
		return list(filter(lambda f: not os.path.isdir(f), files))

	def run(self):
		# Discovering local files in local path
		files = self._discoverLocalFiles()

		# Creating local resting path. This is the local path + resting path.
		localRestingPath = os.path.join(self.localPath, self.restingPath)
		self.status.emit(f'Creating local resting path `{localRestingPath}`...')
		os.makedirs(localRestingPath, exist_ok=True)

		# Generating a new auth token
		self.generateAuthToken()

		# For each of the files
		for counter, filename in enumerate(files):
			try:
				# Generating a new upload link
				uploadLinkRequest = self.getUploadLink(self.remotePath)

				### Checking the link for common errors ########################
				# Checking if folder exists
				if uploadLinkRequest.status_code == 404:
					# Creating the remote folder
					self.makeRemoteDirectory(self.remotePath)

					# Trying the upload link again
					uploadLinkRequest = self.getUploadLink(self.remotePath)

				# Checking the upload link request then converting it to something useful
				uploadLinkRequest.raise_for_status()
				uploadLink = uploadLinkRequest.json()

				### Actually uploading the file ################################
				# Finding the basename of the file
				basename = os.path.basename(filename)
				self.status.emit(f'Uploading {filename}...')

				# Creating a upload request
				uploadRequest = requests.post(
					uploadLink,
					data={'filename': basename, 'parent_dir': self.uploadPath},
					files={'file': open(filename, 'rb')},
					headers={'Authorization': f'Token {self.token}'},
				)
				# Checking the upload request
				uploadRequest.raise_for_status()

				# Moving the folder on the local system
				destination = self.findUnusedName(os.path.join(self.localPath, self.restingPath), basename)
				os.rename(filename, destination)

				# Logging the upload progress on the progress bar
				self.progress.emit((counter + 1.0) / len(files))

			# Catching all kinds of exceptions and printing out the stacktrace
			except Exception as exc:
				import traceback
				traceback.print_exc()
				self.error.emit(exc)
				return

		self.complete.emit()

	def findUnusedName(self, folder, name, maxItr=999):
		# If the file exists in the upload folder, we'll need to find a different name to use
		nameParts = name.split('.')
		rootName = '.'.join(nameParts[0:-1])
		ext = nameParts[-1]

		destination = os.path.join(folder, name)
		for i in range(1, maxItr):
			if not os.path.isfile(destination):
				break

			destination = os.path.join(folder, f'{rootName}-{i}.{ext}')

		return destination


class SeafileUploader(QtCore.QObject):
	''' A QObject that uploads files in a given path to a seafile server.

	QSignals:
		progress (float): The percentage or status of the uploader.
		status (str): Current string status for the uploader. Useful for user UI's.
		complete: Is called when the uploader has finished uploading all the files.
		error (object): Is called if there was any error when uploading the files.
	'''
	progress = QtCore.Signal(float)
	status = QtCore.Signal(str)
	complete = QtCore.Signal()
	error = QtCore.Signal(object)

	def __init__(self, parent=None, configFilePath=None, **kwargs):
		''' A QObject that, when given a path, repoID, and some type of authorization, will upload all files in a directory to a seafile repository.

		Parameters:
			parent ([obj] QObject): QT parent.
			configFilePath ([obj] path, None): Path to the config file. The SeafileUploader will take keyword arguments form this file following .ini methods.

		Keyword Parameters:
			local_path (str): Path (usually a folder) to upload all files to the Seafile repo.
			remote_path (str): Path to place these files on the Seafile repo.
			repo_id (str): Repository ID given from the seafile library.
			username (str): Username for the account that you are uploading files from. Reccomend to use a specific account (Not your own) to upload files from).
			password (str): Password for the account that you are uploading files from.
			[resting_path] (str, 'uploaded'): Path to place the files once they have been uploaded. This is relative to the local files path.
		'''
		super().__init__(parent)

		# Creating the thread variable
		self._uploadThread = None

		# Reading in settings from the configFilePath
		settings = {}
		if configFilePath is not None:
			savedInfo = configparser.ConfigParser()
			savedInfo.read(configFilePath)
			for _,section in savedInfo.items():
				for k,v in section.items():
					print(f'`{k}` | `{v}`')
					settings[k] = v

		# Creating the kwargs dictionary
		self._keywordArguments = {**settings, **kwargs}

	def start(self):
		''' Call this method to start the uploading process.'''
		# Waiting for the old thread to finish if one already exists
		if self._uploadThread is not None:
			self._uploadThread.wait()

		# Creating a new upload thread and giving it our arguments
		self._uploadThread = UploadThread(**self._keywordArguments)

		# Connecting thread signals
		self._uploadThread.progress.connect(self.progress.emit)
		self._uploadThread.status.connect(self.status.emit)
		self._uploadThread.error.connect(self.error.emit)
		self._uploadThread.complete.connect(self.complete.emit)

		# Starting the upload thread
		self._uploadThread.start()