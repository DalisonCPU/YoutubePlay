#-*- coding:utf-8 -*-
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details.
# YoutubePlay - Script destinado à reprodução de links do Youtube
# Feito por Dalison J. T
from datetime import datetime
from datetime import timedelta
import threading
from scriptHandler import script
import os, ui
import api
import globalVars
from globalPluginHandler import GlobalPlugin
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
        ui.message(
        # TRANSLATORS: Mensagem para anunciar que não encontrou o link
        _("Link não encontrado."))
        return
    final = ""
    if link.find("https://")>-1:
        final = link.split("https://")[1]
    elif link.find("HTTPS://")>-1:
        final = link.split("HTTPS://")[1]
    else:
        final = ""
    if final == "":
        ui.message(
        # TRANSLATORS: Mensagem para anunciar que não encontrou o link
        _("Link não encontrado."))
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
            ui.message(
            # TRANSLATORS: Mensagem que anuncia que nenhum link foi retornado do Youtube-dl
            _("Nenhum link retornado do Youtube-dl"))
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

class GlobalPlugin(GlobalPlugin):
    scriptCategory = _("YoutubePlay")
    def __init__(self):
        if globalVars.appArgs.secure:
            return
        super(GlobalPlugin, self).__init__()
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

    @script(
        description=
        # TRANSLATORS: Nome que aparece nos gestos de entrada ao definir comandos do NVDA
        _("Tenta reproduzir um link da área de transferência"),
        gestures=["kb:NVDA+CONTROL+SHIFT+H"]
    )
    def script_reproduzVideo(self, gesture):
        global _handle
        info = pybass.BASS_ChannelIsActive(_handle)
        if info == pybass.BASS_ACTIVE_PLAYING:
            pybass.BASS_ChannelStop(_handle)
            _handle = 0
        th = threading.Thread(target=buscaLink, daemon=True)
        th.start()

    @script(
        description=
        # TRANSLATORS: Nome que aparece em definir comandos, ao chamar a função para pausar ou reproduzir o vídeo atual
        _("Pausa ou reproduz o vídeo atual"),
        gestures=["kb:NVDA+CONTROL+SHIFT+K"]
    )
    def script_alternaVideo(self, gesture):
        global _handle
        info = pybass.BASS_ChannelIsActive(_handle)
        if info ==pybass.BASS_ACTIVE_PLAYING:
            pybass.BASS_ChannelPause(_handle)
        else:
            pybass.BASS_ChannelPlay(_handle, False)

    @script(
        description=
        # TRANSLATORS: Nome mostrado em definir comandos ao alterar o comando para abaixar volume
        _("Abaixa o volume da música em reprodução"),
        gestures=["kb:NVDA+CONTROL+SHIFT+J"]
    )
    def script_abaixaVolume(self, gesture):
        global _handle, volume
        info = pybass.BASS_ChannelIsActive(_handle)
        if info !=pybass.BASS_ACTIVE_PLAYING:
            return
        volume = volume - 200
        setVolume()

    @script(
        description=
        # TRANSLATORS: Nome mostrado em definir comandos ao alterar o comando para aumentar volume
        _("Aumenta o volume do vídeo em reprodução"),
        gestures=["kb:NVDA+CONTROL+SHIFT+L"]
    )
    def script_aumentaVolume(self, gesture):
        global _handle, volume
        info = pybass.BASS_ChannelIsActive(_handle)
        if info !=pybass.BASS_ACTIVE_PLAYING:
            return
        volume = volume + 200
        setVolume()


    def terminate(self):
        if _handle !=0:
            pybass.BASS_StreamFree(_handle)
        pybass.BASS_Free()
