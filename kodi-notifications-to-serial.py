#!/usr/bin/python
# -*- coding: latin-1 -*-

# Verbindet sich per TCP an den KODI JSON-RPC TCP Port 9090
# Empfängt NotfiyALL Notifications
# Setzt die Notifications in Aufrufe an eine Serielle Schnittstelle um


# Schritte:
# TCP Client, der von Kodi empfängt
# JSON Decoder, der die Notifications dekodiert
# Mapping, welches die Ntifications in serielle Befehle umsetzt
# Befehle, um die Kommandos an die serielle Schnittstelle zu schicken

import serial
import socket
import time

# kodi Verbindungsparameter
kodihost = "192.168.178.62"
kodiport = 9090

# diese Kommandos werden an den Receiver geschickt
cmd_up = "07a1a"
cmd_down = "07a1b"
cmd_ready = "\x11000\x03"
cmd_reset = "\x13\x7f\x7f\x7f\x03"
thx = "\x02207e82\x03" + "\x0207ec2"
stereo = "07ec0"
pure_on = "07e80"
pure_off = "07e82"
amp_on  =  "07a1d"
amp_off =  "07a1e"
cmd_zone1on =  "07e7e"

lastmode="ficker"

# befehle in dieser liste werden ignoriert, wenn sie mehrfach hintereinander kommen
modelist = ['music']

# {"jsonrpc":"2.0","method":"Other.LAUTER","params":{"data":null,"sender":"FUCK"}}
kommandoliste  = {
        "LAUTER": cmd_up,
        "LEISER": cmd_down,
	"movie": thx,
	"episode": thx,
	"liveTV": thx,
	"channel": thx,
	"stream": thx,
	"musicvideo": stereo,
	"music": pure_on,
	"ampon": amp_on,
	"ampoff": amp_off,
        "cmdready": cmd_ready,
        "cmdreset": cmd_reset,
        "cmdzone1on" : cmd_zone1on,
        }


###
###
###

# Der RX-V1600 nimmt folgende Einstellungen an:
# 9600,8,N,1
# Serielle Verbindung öffnen
# variable: dose
serielleverbindung = serial.Serial(
        port='/dev/ttyAMA0',
        baudrate=9600,
)

def receiversend(cmd="",prefix="\x02", suffix="\x03"):
    if not('\x11' in cmd or '\x12' in cmd or '\x13' in cmd or '\x03' in cmd or '\x02' in cmd): 
        serielleverbindung.write(prefix)
    serielleverbindung.write(cmd)
    serielleverbindung.write(suffix)



# initialisiere receiver:
#(war in versuchen nicht notwendig)
#serielleverbindung.write(kommandoliste['cmdready'])
receiversend(kommandoliste['cmdready'])

# baue tcp verbindung zu kodi auf um notifications zu empfangen
# variable: socke
kodiverbindung = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
kodiverbindung.connect((kodihost,kodiport))


# beim scriptstart den verstärker pauschal anschalten
# 07e7e
#serielleverbindung.write(kommandoliste['ampon'])
#serielleverbindung.write(kommandoliste['cmdzone1on'])

receiversend(kommandoliste['cmdzone1on'])
time.sleep(1)

# endlosschleife, empfange von socke, schreibe nach dose
while 1:
    empfangenedaten = kodiverbindung.recv(1024)
    #print "empfangen: " + empfangenedaten

    for kommandoname in kommandoliste:
        if kommandoname in empfangenedaten:
            print "TREFFER:" + kommandoname
            if kommandoname == lastmode and kommandoname in modelist:
                print "same as before, ignoring"
            else:
                receiversend(kommandoliste[kommandoname])

            lastmode=kommandoname


