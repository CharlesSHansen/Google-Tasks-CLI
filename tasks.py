from __future__ import print_function
import sys
import httplib2
import os
import json

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
	import argparse
	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None

SCOPES = 'https://www.googleapis.com/auth/tasks'
CLIENT_SECRET_FILE = '.client_secret.json'
APPLICATION_NAME = 'Google Tasks CLI'
__author = 'cshansen'

def raw_in(message):
	"""	Utilizes raw_input to get input from the command line from the user.
	
	Handles ctrl+d to end the program.

	Returns:
		rawinput, the raw input from the command line from the user
	"""
	try:
		rawinput = raw_input(message)
	except:
		print('Quit\n')
		sys.exit()		
	return rawinput

def get_credentials():
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
		Credentials, the obtained credential.
	"""
	home_dir = os.path.expanduser('~')
	credential_dir = os.path.join(home_dir, '.google-credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir,
								   'tasks-cli.json')

	store = oauth2client.file.Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

def add_task(intcommand, item, service):
	toadd = { 'title':  intcommand[1] }
	added = service.tasks().insert(tasklist=item['id'], body=toadd).execute()
	print('Task {0} added.'.format(added['title']))

def delete_task(rawcommand, alltasks, item, service):
	todelete = 0
	fincommand = rawcommand.split(' ')
	try:
		for i in range(1, len(fincommand)):
			for task in alltasks:
				if(todelete == int(fincommand[i])):
					deleted = service.tasks().delete(tasklist=item['id'], task=task['id']).execute()
					print('Task Deleted.')
				todelete += 1
			todelete = 0
	except:
		pass


def complete_task(rawcommand, alltasks, item, service):
	tocomplete = 0
	fincommand = rawcommand.split(' ')
	for i in range(1, len(fincommand)):
		try:
			for task in alltasks:
				if(tocomplete == int(fincommand[i])):
					toupdate = service.tasks().get(tasklist=item['id'], task=task['id']).execute()
					toupdate['status'] = 'completed'
					updated = service.tasks().update(tasklist=item['id'], task=task['id'], body=toupdate).execute()
					print('Task {0} completed. Good job!'.format(updated['title']))
				tocomplete += 1
			tocomplete = 0
		except:
			pass

def reopen_task(rawcommand, alltasks, item, service):				
	toreopen = 0
	fincommand = rawcommand.split(' ')
	try:
		for i in range(1, len(fincommand)):
			for task in alltasks:
				if(toreopen == int(fincommand[i])):
					toupdate = service.tasks().get(tasklist=item['id'], task=task['id']).execute()
					toupdate['status'] = 'needsAction'
					toupdate['completed'] = None
					updated = service.tasks().update(tasklist=item['id'], task=task['id'], body=toupdate).execute()
					print('Task {0} updated.'.format(updated['title']))
				toreopen += 1
			toreopen = 0
	except:
		pass

def expanded_task(command, alltasks):
	disp = 0
	for disptask in alltasks:
		if(disp == int(command)):
			title = disptask['title']
			status = disptask['status']
			try:
				due = disptask['due']
			except:
				due = 'No Due Date'
			try:
				notes = disptask['notes']
			except:
				notes = 'No notes'
			print('\n{0}:\t{1}\n\tDue: {2}\n\t{3}\n'.format(title, status, due, notes))

		disp += 1


def main():
	"""Shows basic usage of the Google Tasks API.

	Creates a Google Tasks API service object and outputs the first 10
	task lists.
	"""
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('tasks', 'v1', http=http)

	results = service.tasklists().list(maxResults=10).execute()
	items = results.get('items', [])
	if not items:
		print('No task lists found.')
		return
	else:
		print('Task lists:')
		order = 0
		for item in items:
			print('[{0}] {1}'.format(order, item['title']))
			order += 1
		rawlist = raw_in('Which list would you like to use? ')
		listnum = -1
		valid = 0

		"""
		Show available lists and have user select one
		"""
		for item in items:
			listnum += 1
			try:
				if(int(rawlist) == listnum):
					valid = 1
			except:
				if(rawlist.lower() == item['title'].lower()):
					valid=1

			"""
			List commands and prompt user for action
			"""
			if(valid):
				while(1):
					tasklist = service.tasks().list(tasklist=item['id']).execute()
					alltasks = tasklist.get('items', [])
					order = 0
					for task in alltasks:
						print('[{0}] {1} ({2})'.format(order, task['title'], task['status']))
						order += 1
					rawcommand = raw_in('What action would you like to take? ')
					intcommand = rawcommand.split(' ', 1)
					command = intcommand[0]
		

					if(command.lower() == 'add' or command.lower() == 'a'):
						add_task(intcommand, item, service)

					elif(command.lower() == 'delete' or command.lower() == 'd'):
						delete_task(rawcommand, alltasks, item, service)

					elif(command.lower() == 'complete' or command.lower() == 'c'):
						complete_task(rawcommand, alltasks, item, service)
						
					elif(command.lower() == 'reopen' or command.lower() == 'r'):
						reopen_task(rawcommand, alltasks, item, service)

					elif(command.lower() == 'quit' or command.lower() == 'q'):
						return

					elif(command.isdigit()):
						if(int(command) <= len(alltasks) - 1):
							expanded_task(command, alltasks)

					else:
						print("Commands are: add, delete, complete, reopen, quit")

if __name__ == '__main__':
	main()