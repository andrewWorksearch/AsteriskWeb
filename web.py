#!/usr/bin/env python3

from random import choice
from string import ascii_uppercase
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options
from urllib.parse import urlencode, quote_plus
from configparser import ConfigParser
import hashlib
import socket
import pymysql
import pickle
import requests
import json
import datetime
import time
import os
import sys

def config(section):
	direct='%s/config.ini'%os.path.realpath(os.path.dirname(sys.argv[0]))
	parser = ConfigParser()
	parser.read(direct)
	params = {}
	if parser.has_section(section):
		items = parser.items(section)
		for item in items:
			params[item[0]] = item[1]
	return params

def cdrConnect(code):  
	data = []
	code = ';'.join([code])
	connect = config('cdr')
	conn = pymysql.connect(**connect)
	cursor = conn.cursor(pymysql.cursors.DictCursor)
	cursor.execute(code)
	for item in cursor.fetchall():
		data.append({'src':item['src'],'dst':item['dst'],'duration':item['billsec'],'uid':item['uniqueid'],'record':item['mixmonitor_filename']})
	cursor.close()
	conn.close()
	return data

def accountsConnect(code):  
	code = ';'.join([code])
	connect = config('accounts')
	conn = pymysql.connect(**connect)
	cursor = conn.cursor(pymysql.cursors.DictCursor)
	cursor.execute(code)
	conn.commit()
	data = cursor.fetchone()
	cursor.close()
	conn.close()
	return data

class MainHandler(tornado.web.RequestHandler):	
	def get(self):
		if not self.get_secure_cookie("token"):
			self.redirect("/login")
		else:
			self.redirect("/%s"%self.get_cookie("office"))

class LoginHandler(tornado.web.RequestHandler):
	def get(self):
		if not self.get_secure_cookie("token"):
			self.render("auth.html")
		else:
			self.redirect("/%s"%self.get_cookie("office"))
	def post(self):
		username = self.get_argument('username')
		passwd = hashlib.md5(self.get_argument('passwd').encode()).hexdigest()
		code = "Select token,office from accounts where login='%s' and passwd='%s';"%(username,passwd)
		user = accountsConnect(code)
		if not user['token']:
			self.write('user does not exist')
		if user['token']:
			self.set_secure_cookie("token", user['token'])
			self.set_cookie("office", str(user['office']))
			self.write('success')

class UserHandler(tornado.web.RequestHandler):
	def get(self,number):
		if self.get_secure_cookie("token"):
			code = 'Select *  from accounts where token="%s";'%(self.get_secure_cookie("token").decode())
			user = accountsConnect(code)
			settings = {'context':user['context'],'outline':user['outline'],'SIP':'','PJSIP':'','IAX':''}
			if user['protocol'] == 'SIP':
				settings['SIP'] = 'selected'
			if user['protocol'] == 'PJSIP':
				settings['PJSIP'] = 'selected'
			if user['protocol'] == 'IAX':
				settings['IAX'] = 'selected'
			self.render("main.html",settings = settings)
		else:
			self.redirect("/login")

class CallHandler(tornado.web.RequestHandler):
	def Call(self,src,dst,callerid,context,variable):
		ami = socket.socket()
		HOST = config('asterisk').get('host')
		PORT = int(config('asterisk').get('port'))
		ami.connect((HOST, PORT))
		ami.settimeout(1)
		ami.send(b'''Action: login
Username: %b
Secret: %b

'''%(config('asterisk').get('username').encode(),config('asterisk').get('password').encode()))
		ami.send(b'''Action: Originate
Channel: %b
Exten: %b
Context: %b
Priority: 1
Variable: %b
Callerid: %b
Async: Yes

'''%(src.encode(),dst.encode(),context.encode(),variable.encode(),callerid.encode()))
		byteraw = b''
		while True:
			try:
				byteraw += ami.recv(1024)
			except socket.timeout:
				break


	def post(self):
		self.add_header('Access-Control-Allow-Origin','*')
		src = self.get_argument('from')
		dst = self.get_argument('to')
		context = self.get_argument('context')
		callerid = self.get_argument('as')
		variable = self.get_argument('variable')
		self.Call(src,dst,callerid,context,variable)

class SpyHandler(tornado.web.RequestHandler):
	def chanSpy(self,src,dst):
		ami = socket.socket()
		HOST = config('asterisk').get('host')
		PORT = int(config('asterisk').get('port'))
		ami.connect((HOST, PORT))
		ami.settimeout(1)
		ami.send(b'''Action: login
Username: %b
Secret: %b

'''%(config('asterisk').get('username').encode(),config('asterisk').get('password').encode()))
		ami.send(b'''Action: Originate
Channel: %b
Application: ChanSpy
Data: %b,bBx
Callerid: "ChanSpy"

'''%(src.encode(),dst.encode()))
		byteraw = b''
		while True:
			try:
				byteraw += ami.recv(1024)
			except socket.timeout:
				break

	def post(self):
		self.add_header('Access-Control-Allow-Origin','*')
		src = self.get_argument('from')
		dst = self.get_argument('to')
		self.chanSpy(src,dst)

class StatusHandler(tornado.web.RequestHandler):
	def Status(self):
		ami = socket.socket()
		HOST = config('asterisk').get('host')
		PORT = int(config('asterisk').get('port'))
		ami.connect((HOST, PORT))
		ami.settimeout(1)
		ami.send(b'''Action: login
Username: %b
Secret: %b

'''%(config('asterisk').get('username').encode(),config('asterisk').get('password').encode()))
		ami.send(b'Action: Status\r\n\r\n')
		byteraw = b''
		while True:
			try:
				byteraw += ami.recv(1024)
			except socket.timeout:
				break
		data = []
		for items in byteraw.split(b'\r\n\r\n'):
			dict = {}
			if items:
				for item in items.split(b'\r\n'):
					item = item.decode()
					try:
						dict['%s'%item.split(':')[0].strip()] = item.split(':')[1].strip()
					except IndexError:
						pass
				try:
					if dict['Event'] == 'Status':
						data.append(dict)
				except KeyError:
					pass
		return {'Status': data}

	def get(self):
		self.write(self.Status())

class ChangeHandler(tornado.web.RequestHandler):
	def post(self):
		context = self.get_argument('context')
		protocol = self.get_argument('protocol')
		outline = self.get_argument('outline')
		token = self.get_secure_cookie('token').decode()
		code = "update accounts set protocol = '%s',context = '%s', outline = '%s' where token='%s';"%(protocol,context,outline,token)
		accountsConnect(code)

class AddUserHandler(tornado.web.RequestHandler):
	def post(self):
		login = self.get_argument('login')
		passwd = hashlib.md5(self.get_argument('passwd').encode()).hexdigest()
		office = self.get_argument('office')
		token = ''.join(choice(ascii_uppercase) for i in range(32))
		code = "insert into accounts (login,passwd,office,token,context,outline,protocol) values ('%s','%s',%s,'%s','','','SIP');"%(login,passwd,office,token)
		accountsConnect(code)

class ChangePasswdHandler(tornado.web.RequestHandler):
	def post(self):
		passwd = hashlib.md5(self.get_argument('passwd').encode()).hexdigest()
		token = self.get_secure_cookie('token').decode()
		code = "update accounts set passwd = '%s' where token='%s';"%(passwd,token)
		accountsConnect(code)

# class AmoHandler(tornado.web.RequestHandler):

def main():
	tornado.options.parse_command_line()
	settings = {"static_path": os.path.join(os.path.dirname(__file__), "static")}		
	application = tornado.web.Application([
		(r"/", MainHandler),
		(r"/login", LoginHandler),
		(r"/([0-9]+)", UserHandler),
		(r"/api/call", CallHandler),
		(r"/api/chanspy", SpyHandler),
		(r"/api/status", StatusHandler),
		(r"/change", ChangeHandler),
		(r"/adduser", AddUserHandler),
		(r"/changepasswd", ChangePasswdHandler),
		# (r"/api/amo", AmoHandler)
	], **settings, cookie_secret="n543AXvWNN8ZkQXZR229gnRgnXlnUmqEIAwwcXqc/Vo=")
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(config('server').get('port'),config('server').get('host'))
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()