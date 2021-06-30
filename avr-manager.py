#!/usr/bin/python3

# Licensed under GNU GPLv3, see LICENSE file

import pyudev
import requests
import xml.etree.ElementTree as ET
import pygame
from multiprocessing import Process

url = 'http://Yamaha-AVR/YamahaRemoteControl/ctrl'
get_info_xml = '<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>'
switch_input_xml = '<?xml version="1.0" encoding="utf-8"?><YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>$INPUT$</Input_Sel></Input></Main_Zone></YAMAHA_AV>'
target_input = 'HDMI1'
last_input_file_path = '/home/pi/last_input.txt'
sound_file_connect_path = '/home/pi/raspi-bt-hd-audio-receiver/sounds/connected.mp3'
sound_file_disconnect_path = '/home/pi/raspi-bt-hd-audio-receiver/sounds/disconnected.mp3'

def switch_input(input_target):
	payload = switch_input_xml.replace("$INPUT$", input_target)
	res = requests.post(url, data = payload)

def get_device_info():
	return requests.post(url, data = get_info_xml)

def get_current_input():
	res = get_device_info().text
	parsed = ET.fromstring(res)
	main_zone = parsed.find('Main_Zone')
	basic_status = main_zone.find('Basic_Status')
	inp = basic_status.find('Input')
	input_sel = inp.find('Input_Sel')

	current_input = input_sel.text

	return current_input

def get_last_input():
	f = open(last_input_file_path, 'r')
	first_line = f.readline().strip()
	return first_line 

def set_last_input(inp):
	f = open(last_input_file_path, 'w')
	f.write(inp)
	f.close()

def play_sound(file):
	pygame.mixer.init()
	pygame.mixer.music.load(file)
	pygame.mixer.music.play()
	while pygame.mixer.music.get_busy() == True:
		continue

context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by(subsystem='input')

for device in iter(monitor.poll, None):
	if device.action == 'add':
		current_input = get_current_input()
		if current_input != target_input:
			set_last_input(current_input)
			switch_input(target_input)
		Process(target=play_sound(sound_file_connect_path)).start()

	if device.action == 'remove':
		current_input = get_current_input()
		if current_input == target_input:
			Process(target=play_sound(sound_file_disconnect_path)).start()
			switch_input(get_last_input())