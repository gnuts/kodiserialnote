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
import json
import syslog
import time

# kodi Verbindungsparameter
kodihost = "192.168.178.62"
kodiport = 9090

# diese Kommandos werden an den Receiver geschickt
cmd_up = "07a1a"
cmd_down = "07a1b"
cmd_ready = "\x11000\x03"
cmd_reset = "\x13\x7f\x7f\x7f\x03"
thx = "\x0207e82\x03" + "\x0207ec2"
stereo = "07ec0"
pure_on = "07e80"
pure_off = "07e82"
amp_on  =  "07a1d"
amp_off =  "07a1e"
cmd_zone1on =  "07e7e"
initamp_on  =  cmd_ready + "\x03\x02" + cmd_zone1on


# befehle in d]ieser liste werden ignoriert, wenn sie mehrfach hintereinander kommen
medialist = ['music','movie','episode','liveTV', 'channel', 'stream','musicvideo']
senderlist = ['FUCK','kodi.callbacks']
methodlist = ['Other.LAUTER','Other.LEISER','Other.onScreensaverDeactivated','other.ampon','Other.ampoff']

# {"jsonrpc":"2.0","method":"Other.LAUTER","params":{"data":null,"sender":"FUCK"}}
kommandoliste  = {
        'Other.LAUTER': cmd_up,
        'Other.LEISER': cmd_down,
	'movie': thx,
	'episode': thx,
	'liveTV': thx,
	'channel': thx,
	'stream': thx,
	'musicvideo': stereo,
	'music': pure_on,
        'Other.ampoff': amp_off,
        'Other.onScreensaverDeactivated': initamp_on,
        'other.ampon': initamp_on,
        'cmdready': cmd_ready,
        'cmdreset': cmd_reset,
        'cmdzone1on' : cmd_zone1on,
        }


###
###
###

def LOG(text):
    syslog.syslog(text)

def mainloop():
    lastmedia="ficker"

    # Der RX-V1600 nimmt folgende Einstellungen an:
    # 9600,8,N,1
    # Serielle Verbindung öffnen
    # variable: dose
    serielleverbindung = serial.Serial(
            port='/dev/ttyAMA0',
            baudrate=9600,
    )
    LOG("Serielle Verbinung hergestellt")
    
    def receiversend(cmd="",prefix="\x02", suffix="\x03"):
       if not('\x11' in cmd or '\x12' in cmd or '\x13' in cmd or '\x03' in cmd or '\x02' in cmd): 
           serielleverbindung.write(prefix)
       serielleverbindung.write(cmd)
       serielleverbindung.write(suffix)
   
     # initialisiere receiver:
    receiversend(kommandoliste['cmdready'])
     # beim scriptstart den verstärker pauschal anschalten
    receiversend(kommandoliste['cmdzone1on'])
    LOG("Verstärker initialisiert")
   
    # baue tcp verbindung zu kodi auf um notifications zu empfangen
    try:
        kodiverbindung = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        kodiverbindung.connect((kodihost,kodiport))
    except:
        LOG("Verbindungsfehler!")
        return
    
    LOG("Verbindung zu Kodi hergestellt, warte auf Eingaben")
    
    # endlosschleife, empfange von socke, schreibe nach dose
    while 1:
        empfangenedaten = kodiverbindung.recv(1024)
    
        if not empfangenedaten:
            LOG("connection lost?")
            break
    
    
        LOG("empfangen: " + empfangenedaten)
    
        # wandle JSON String in Dict um
        try:
            daten = json.loads(empfangenedaten)
        except:
            LOG("fehlerhafte daten. wird ignoriert.")
            continue
    
        if not daten:
            LOG("daten fehlerhaft")
            continue
    
        sendername = daten.get('params',{}).get('sender','UNKNOWN')
        methodname = daten.get('method',"UNKOWN METHOD")
        
        mediatype = "NONE"
        kommandoname = ""
    
        if daten.get('params',{}).get('data',False):
            mediatype = daten.get('params',{}).get('data',{}).get("mediaType",'UNKNOWN')
    
        # wenn es kein "sender" ist, den wir über senderlist abonniert haben, überspringe.
        if sendername not in senderlist:
            LOG("sender " + sendername + " wird ignoriert")
            continue
    
        if mediatype in medialist:
            LOG("MEDIUM:" + mediatype)
            if mediatype == lastmedia and mediatype in medialist:
                LOG("same as before, ignoring")
            else:
                kommandoname = mediatype
    
            lastmedia=mediatype
    
        elif methodname in methodlist:
            LOG("METHOD: " + methodname)
            kommandoname = methodname
    
        if kommandoname:
            receiversend(kommandoliste[kommandoname])
        else:
            LOG("kein Ereignis gefunden.")
    

#
# MAIN
#

while 1:
    LOG("Kodi JSON to Serial gestartet")
    mainloop()
    LOG("Hauptschleife wurde beendet, Neustart in 10 Sekunden...")
    time.sleep(10)
