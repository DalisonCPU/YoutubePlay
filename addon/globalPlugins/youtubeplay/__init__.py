#-*- coding:utf-8 -*-
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details.
# YoutubePlay - Script destinado à reprodução de links do Youtube
# Feito por Dalison J. T
import importlib
from datetime import datetime
from datetime import timedelta
import threading
from scriptHandler import script
import os, ui, wx, gui, winsound
import api
import globalVars
from globalPluginHandler import GlobalPlugin
import addonHandler
import sys
from logHandler import log
dirAddon=os.path.dirname(__file__)
sys.path.append(dirAddon)
try:
	import pybass
	import pybass_aac
except:
	log.exception(
		# TRANSLATORS: Erro ao importar bass
		_("Erro ao importar a biblioteca bass"))
sys.path.append(os.path.join(dirAddon, "lib"))
try:
	import xml
	xml.__path__.append(os.path.join(dirAddon, "lib", "xml"))
	import importlib_metadata
	importlib_metadata.__path__.append(os.path.join(dirAddon, "lib", "importlib_metadata"))
	import html
	html.__path__.append(os.path.join(dirAddon, "lib", "html"))
	import markdown
	markdown.__path__.append(os.path.join(dirAddon, "lib", "markdown"))
	import urllib.request
	import json
	import zipfile
except:
	log.exception(
		# TRANSLATORS: Mensagem que será mostrada no log caso ocorra algum erro de importação com as bibliotecas do YoutubeDL
		_("Erro ao importar uma ou mais bibliotecas usadas no YoutubeDL"))
import youtube_dl
try:
	import distutils
	distutils.__path__.append(os.path.join(dirAddon, "lib", "distutils"))
	from distutils.dir_util import copy_tree
	from shutil import rmtree
except:
	log.exception(
		# TRANSLATORS: Mensagem mostrada no log, caso alguma biblioteca usada para a atualização do addon não seja importada.
		_("Erro ao importar uma ou mais bibliotecas usadas para a atualização do YoutubeDL."))
del sys.path[-1]
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

def __call__(block_num, block_size, total_size):
    # Esta función se podria definir para tener un contador de bityes descargados y porcentaje.
    # Todo depende de como quieras hacer el actualizador.
    pass

def atualizaYoutubedl():
    # Url para obtener el json y obtener el archivo de descarga de la ultima versión desde el repo oficial de YouTube-Dl
    url = "https://api.github.com/repos/ytdl-org/youtube-dl/releases"
    req = urllib.request.Request(url)
    # Vamos a obtener el json y a leerlo.
    r = urllib.request.urlopen(req).read()
    gitJson = json.loads(r.decode('utf-8'))
    # Vamos a comprobar si la versión de Github es mayor que la que tenemos instalada si lo es descargamos
    if gitJson[0]["tag_name"] != youtube_dl.version.__version__:
        versaoSalva= ""
        if os.path.exists(os.path.join(os.path.dirname(__file__), "version.txt")):
            f = open(os.path.join(os.path.dirname(__file__), "version.txt"), "r")
            versaoSalva = f.readline()
            f.close()
        if versaoSalva !="" and versaoSalva == gitJson[0]["tag_name"]:
            return
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        resposta = wx.MessageBox(_("Você deseja atualizar o YoutubeDl?"), _("Atualização disponível do YoutubeDl"), wx.ICON_QUESTION | wx.YES_NO)
        if resposta != 2:
            f = open(os.path.join(os.path.dirname(__file__), "version.txt"), "w")
            f.write(gitJson[0]["tag_name"])
            f.close()
            return
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(gitJson[0]['zipball_url'], dirAddon+"/test.zip", reporthook=__call__)
        # Ahora leemos el archivo zip descargado que hemos llamado test.zip
        archive = zipfile.ZipFile(dirAddon+'/test.zip')
        # Obtenemos el nombre del directorio raiz del zip, necesario por que cada nueva versión tendra un nombre.
        root = archive.namelist()[0]
        # Esto siguiente buscara el directorio que nos interesa para extraer que es el Youtube_dl. No es necesario por que podemos construirlo con el root pero prefiero por si algun día cambiase.
        filtro = [item for item in archive.namelist() if "youtube_dl".lower() in item.lower()]
        # Ahora vamos a extraer solo el directorio de YouTube-Dl.
        for file in archive.namelist():
            if file.startswith(filtro[0]):
                archive.extract(file, dirAddon)
        archive.close()
    # Borramos el archivo descargado
        os.remove(dirAddon+"/test.zip")
        # Ahora vamos a borrar el directorio de la libreria de youtube_dl
        rmtree(dirAddon+"\\youtube_dl")
        # Ahora vamos a copiar el directorio extraido de youtube_dl a la raiz de nuestro proyecto.
        copy_tree(dirAddon+"\\"+root, dirAddon)
        # Ahora vamos a borrar el directorio que extraimos.
        rmtree(os.path.join(dirAddon, root))
        importlib.reload(youtube_dl)
        if gitJson[0]["tag_name"] != youtube_dl.version.__version__:
            log.error(
                # TRANSLATORS: Mensagem de erro se o YoutubeDL não for atualizado
                _("Por algum motivo o YoutubeDL não foi atualizado."))
        else:
            gui.messageBox(
                # TRANSLATORS: Mensagem mostrada quando concluir a atualização do YoutubeDL
                _("O YoutubeDl foi atualizado com sucesso. Reinicie o NVDA para aplicar as alterações."), 
                # TRANSLATORS: Título da janela de atualização
                _("Atualização concluída"), style=wx.OK | wx.ICON_INFORMATION)

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
        y = youtube_dl.YoutubeDL({
                'quiet': False,
                'format': 'mp4',
        })
        r = y.extract_info(link, download=False)
        link = r['url']
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
        th = threading.Thread(target=atualizaYoutubedl, daemon=True)
        th.start()
        self.o = pybass.BASS_Init(-1, 44100, 0, 0, 0)

    @script(
        description=        # TRANSLATORS: Nome que aparece nos gestos de entrada ao definir comandos do NVDA
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
        description=        # TRANSLATORS: Nome que aparece em definir comandos, ao chamar a função para pausar ou reproduzir o vídeo atual
        _("Pausa ou reproduz a música atual"),
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
        description=        # TRANSLATORS: Nome mostrado em definir comandos ao alterar o comando para abaixar volume
        _("Diminui o volume da música em reprodução"),
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
        description=        # TRANSLATORS: Nome mostrado em definir comandos ao alterar o comando para aumentar volume
        _("Aumenta o volume da música em reprodução"),
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

