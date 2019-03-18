#!/usr/bin/env python36

import seafileUploader
from PySide2 import QtWidgets
from functools import partial
import traceback

def progress(prog):
	print('Progress: %.2f' % (prog*100))

def status(status):
	status = f'Status: {status}'
	button.setText(status)
	print(status)

def complete():
	print(f'Complete!')
	button.setText('Start!')
	button.setDisabled(False)

def start():
	uploader.start()
	button.setDisabled(True)

def error(err):
	print(err)
	traceback.print_stack()

app = QtWidgets.QApplication([])

print('Creating uploader')
uploader = seafileUploader.SeafileUploader(configFilePath='./example.ini')

print('Creating the QWidget')
button = QtWidgets.QPushButton('Start!')
button.clicked.connect(start)
uploader.progress.connect(progress)
uploader.status.connect(status)
uploader.complete.connect(complete)
uploader.error.connect(error)

button.show()
app.exec_()