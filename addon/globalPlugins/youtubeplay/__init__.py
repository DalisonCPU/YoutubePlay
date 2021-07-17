#-*- coding:utf-8 -*-
# YoutubePlay - Script destinado à reprodução de links do Youtube
#Feito por Dalison J. T
from datetime import datetime
from datetime import timedelta
import threading
import appModuleHandler
import os, ui
import api
import globalPluginHandler
import addonHandler
import sys
from logHandler import log
sys.path.append(os.path.dirname(__file__))
import pybass
import pybass_aac
addonHandler.initTranslation()

_handle = 0
volume = 300

def setVolume():
    global volume
    if volume >10000:
        volume = 10000
    if volume <200:
        volume = 200
    pybass.BASS_SetConfig(5, volume)

def atualizaYoutubedl():
    a = os.popen(os.path.join(os.path.dirname(__file__), "youtube-dl.exe --update"))

def buscaLink():
    global _handle, volume
    try:
        link = api.getClipData()
    except:
        ui.message(_("Link não encontrado."))
        return
    final = ""
    if link.find("https://")>-1:
        final = link.split("https://")[1]
    elif link.find("HTTPS://")>-1:
        final = link.split("HTTPS://")[1]
    else:
        final = ""
    if final == "":
        ui.message(_("Link não encontrado."))
        return
    link = final
    if final.find(" ")>-1:
        link = final.split(" ")[0]
    #log.info(link)
    if link.find("youtube")>-1:
        link = "https://"+link
        a = os.popen(os.path.join(os.path.dirname(__file__), "youtube-dl.exe -f \"mp4/m4a/webm\" -g -c -i --geo-bypass -4 --no-cache-dir --no-part --no-warnings "+link))
        #log.info(os.path.join(os.path.dirname(__file__), "youtube-dl.exe -f \"mp4/m4a/webm\" -g -c -i --geo-bypass -4 --no-cache-dir --no-part --no-warnings "+link))
        link = a.read()
        if link == "":
            ui.message(_("Nenhum link retornado do Youtube-dl"))
            return
    _handle = load(link)
    setVolume()
    pybass.BASS_ChannelPlay(_handle, False)

class BassError(Exception):
        """Exception raised when an error occurs and auto_raise_errors is set to True."""

        def __init__(self, code):
                self.code=code
                self.description = pybass.get_error_description(self.code)

        def __str__(self):
                return str(self.code) + ", " + self.description

def raise_error():
        """Raises an exception for the most recent function call, if necessary. None otherwise"""
        error_code = pybass.BASS_ErrorGetCode()
        if error_code > pybass.BASS_OK:
                raise BassError(error_code)

def load(url, offset=0, flags=0, user=None):
        """Creates a bass stream from a URL.
        See the bass documentation for the meaning of these parameters.
        """
        downloadproc = pybass.DOWNLOADPROC(0)
        flags |= pybass.BASS_UNICODE

        #print(url, offset, flags, downloadproc, user)
        handle = pybass.BASS_StreamCreateURL(url, offset, flags, downloadproc, user)
        raise_error()
        return handle

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super(globalPluginHandler.GlobalPlugin, self).__init__()
        agora = datetime.now()
        salva = datetime.now()
        if os.path.exists(os.path.join(os.path.dirname(__file__), "data.txt")):
            f = open(os.path.join(os.path.dirname(__file__), "data.txt"), "r")
            salva = datetime.strptime(f.readline(), "%Y-%m-%d %H:%M:%S.%f")
            f.close()
        else:
            f = open(os.path.join(os.path.dirname(__file__), "data.txt"), "w")
            f.write(str(agora))
            f.close()
        delta = agora - salva
        #log.info(str(delta.days)+" dias")
        if delta.days>0:
            f = open(os.path.join(os.path.dirname(__file__), "data.txt"), "w")
            f.write(str(agora))
            f.close()
            th = threading.Thread(target=atualizaYoutubedl, daemon=True)
            th.start()
        self.o = pybass.BASS_Init(-1, 44100, 0, 0, 0)

    def script_reproduzVideo(self, gesture):
        global _handle
        info = pybass.BASS_ChannelIsActive(_handle)
        if info == pybass.BASS_ACTIVE_PLAYING:
            pybass.BASS_ChannelStop(_handle)
            _handle = 0
        th = threading.Thread(target=buscaLink, daemon=True)
        th.start()

    script_reproduzVideo.__doc__ = _('Reproduz e pausa o vídeo')
    def script_alternaVideo(self, gesture):
        global _handle
        info = pybass.BASS_ChannelIsActive(_handle)
        if info ==pybass.BASS_ACTIVE_PLAYING:
            pybass.BASS_ChannelPause(_handle)
        else:
            pybass.BASS_ChannelPlay(_handle, False)

    script_alternaVideo.__doc__ = _('Pausa ou reproduz o vídeo atual')

    def script_abaixaVolume(self, gesture):
        global _handle, volume
        info = pybass.BASS_ChannelIsActive(_handle)
        if info !=pybass.BASS_ACTIVE_PLAYING:
            return
        volume = volume - 200
        setVolume()

    script_abaixaVolume.__doc__ = _('Abaixa o volume da música em reprodução')
    def script_aumentaVolume(self, gesture):
        global _handle, volume
        info = pybass.BASS_ChannelIsActive(_handle)
        if info !=pybass.BASS_ACTIVE_PLAYING:
            return
        volume = volume + 200
        setVolume()

    script_aumentaVolume.__doc__ = _('Aumenta o volume do vídeo em reprodução')

    def terminate(self):
        pybass.BASS_StreamFree(_handle)
        pybass.BASS_Free()

    __gestures = {
        "kb:nvda+shift+control+h": "reproduzVideo",
        "kb:nvda+shift+control+j": "abaixaVolume",
        "kb:nvda+shift+control+k": "alternaVideo",
        "kb:nvda+shift+control+l": "aumentaVolume",
    }
