#!/usr/bin/env python

from sys import exit, stderr, stdout, stdin
from os import chdir, dup2, fork, getpid, kill, path, remove, setsid, umask
from time import sleep
from atexit import register
from signal import SIGTERM 

class Daemon:
	def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = pidfile
	
	def daemonize(self, DEBUG):
		"""
		do the UNIX double-fork magic, see Stevens' "Advanced 
		Programming in the UNIX Environment" for details (ISBN 0201563177)
		http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
		"""
		try: 
			pid = fork() 
			if pid > 0:
				# exit first parent
				exit(0) 
		except OSError, e: 
			stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
			exit(1)
	
		# decouple from parent environment
		chdir("/") 
		setsid() 
		umask(0) 
	
		# do second fork
		try: 
			pid = fork() 
			if pid > 0:
				# exit from second parent
				exit(0) 
		except OSError, e: 
			stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
			exit(1) 
	
		# redirect standard file descriptors
		if DEBUG == False:
			stdout.flush()
			stderr.flush()
			si = file(self.stdin, 'r')
			so = file(self.stdout, 'a+')
			se = file(self.stderr, 'a+', 0)
			dup2(si.fileno(), stdin.fileno())
			dup2(so.fileno(), stdout.fileno())
			dup2(se.fileno(), stderr.fileno())
		else:
			print "\nRunning the service in debug mode."
	
		# write pidfile
		register(self.delpid)
		pid = str(getpid())
		file(self.pidfile,'w+').write("%s\n" % pid)
	
	def delpid(self):
		remove(self.pidfile)

	def start(self, DEBUG):
		# Check for a pidfile to see if the daemon already runs
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
	
		if pid:
			message = "pidfile %s already exist. Daemon already running?\n"
			stderr.write(message % self.pidfile)
			exit(1)
		
		# Start the daemon
		self.daemonize(DEBUG)
		self.run()

	def stop(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
	
		if not pid:
			message = "pidfile %s does not exist. Daemon not running?\n"
			stderr.write(message % self.pidfile)
			return # not an error in a restart

		# Try killing the daemon process	
		try:
			while 1:
				kill(pid, SIGTERM)
				sleep(0.1)
		except OSError, err:
			err = str(err)
			if err.find("No such process") > 0:
				if path.exists(self.pidfile):
					remove(self.pidfile)
			else:
				print str(err)
				exit(1)

	def restart(self, DEBUG):
		self.stop()
		self.start(DEBUG)