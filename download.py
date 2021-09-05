import moviepy.editor as mp
from pytube import YouTube
from pytube import Playlist
import pytube.exceptions
import sys
from pathlib import Path
import re
import os
from googleapiclient.discovery import build
import urllib
import configparser


#Constants
read_config = configparser.ConfigParser()
read_config.read('private.ini')
api_key = read_config.get('API KEY', 'key')


class util():

  def to_screen(*text):
    print(*text)

  def error_screen(*error):
    print(*error)

class Search():
  def __init__(self, developerKey, search):
    self.youtube = build('youtube', 'v3', developerKey=developerKey)
    self.response = self.__searchResult(search)

  def __searchResult(self, search):
    request = self.youtube.search().list(
      part='snippet', 
      maxResults=10, 
      q=search
    )
    response = request.execute()
    return response

  def resultVideoInfo(self, i):
    videoInfo = {}
    
    items = self.response['items']
    videoInfo['videoId'] = items[i]['id']['videoId']
    videoInfo['title'] = items[i]['snippet']['title']
    videoInfo['description'] = items[i]['snippet']['description']
    return videoInfo


class Download():
  TRY_LINK_TIMES = 3
  OPTIONS = {
    'AUDIO_OPT':'mp3', 
    'VIDEO_OPT':'vid', 
    'SEARCH_OPT':'search'
  }

  def downloadAudio(video, location, filename):
    for i in range(Download.TRY_LINK_TIMES):
      try:
        stream = video.streams.filter(only_audio=True, file_extension='mp4').first()
        break
      except urllib.error.HTTPError:
        util.error_screen('Error - HTTP access denied. Retrying...')
      
    for i in range(Download.TRY_LINK_TIMES):
      try:
        mp4_loc = stream.download(output_path=location, filename=filename, max_retries=5)
        break
      except pytube.exceptions.VideoUnavailable:
        util.error_screen('Error - Video Cannot Be Found. Retrying...')

    audio = mp.AudioFileClip(mp4_loc)
    audio.write_audiofile(mp4_loc[:-4] + ".mp3")
    audio.close()
    os.remove(mp4_loc)

  def downloadVideo(video, location, filename):
    for i in range(Download.TRY_LINK_TIMES):
      try:
        stream = video.streams.get_by_itag(22)
        if stream is None:
          stream = video.streams.filter(progressive=True).first()
        break
      except urllib.error.HTTPError:
        util.error_screen('Error - HTTP access denied. Retrying...')
    for i in range(Download.TRY_LINK_TIMES):
      try:
        stream.download(output_path=location, filename=filename, max_retries=5)
        break
      except pytube.exceptions.VideoUnavailable:
        util.error_screen('Error - Video Cannot Be Found. Retrying...')

  def downloadPlaylist(media_type, video, location, filename):
    location += filename + '/'
    
    if media_type == Download.OPTIONS['AUDIO_OPT']:
      for track in video.videos:
        yt = YouTube(track.watch_url)
        print(yt.title)
        Download.downloadAudio(track, location, yt.title)
    elif media_type == Download.OPTIONS['VIDEO_OPT']:
      for track in video.videos:
        Download.downloadVideo(track, location, track.title)
    
  def checkPlayList(link):
    return True if 'playlist?' in link else False


class Launchpad():
  def __init__(self):
    self.link = None
    self.filename = None
    self.location = None
    self.media_type = Download.OPTIONS['AUDIO_OPT']
    self.options = {
      '-'+Download.OPTIONS['SEARCH_OPT']:self.search, 
      '-'+Download.OPTIONS['AUDIO_OPT']:self.audio, 
      '-'+Download.OPTIONS['VIDEO_OPT']:self.video
    }

  def __call__(self):
    for option in self.options.values():
      option()

    if self.link is None:
      found = False
      for arg in sys.argv:
        if arg[0] != '-' and 'youtube.com' in arg:
          self.link = arg
          found = True
      if not found:
        util.error_screen('Video Link Not Found')
        exit()
    
    if self.filename is None:
      for arg in reversed(sys.argv[1:]):
        if arg[0] != '-' and 'youtube.com' not in arg:
          self.filename = arg
          break

    video = None
    isPlaylist = False
    try:
      if Download.checkPlayList(self.link):
        isPlaylist = True
        video = Playlist(self.link)
        self.filename = video.title if self.filename == None else self.filename
      else:
        video = YouTube(self.link)
        self.filename = video.title if self.filename == None else self.filename
    except pytube.exceptions.VideoUnavailable:
      util.error_screen('Bad Link Error')
      exit()

    home = str(Path.home())
    while True:
      self.location = input('Location? (Downloads; Music; Custom): ').upper()
      if self.location == 'DOWNLOADS':
        self.location = home + '/Downloads/'
        break
      elif self.location == 'MUSIC':
        self.location = home + '/Downloads/Music/'
        break
      elif self.location == 'CUSTOM':
        self.location = home + '/' + input('Path to Custom Location: ') + '/'
        break
      else:
        util.to_screen('Type an option')

    if isPlaylist:
      Download.downloadPlaylist(self.media_type, video, self.location, self.filename)
    else:
      if self.media_type == Download.OPTIONS['AUDIO_OPT']:
        Download.downloadAudio(video, self.location, self.filename)
      elif self.media_type == Download.OPTIONS['VIDEO_OPT']:
        Download.downloadVideo(video, self.location, self.filename)

  def __showVideoInfo(self, videoInfo):
    util.to_screen(videoInfo['title'])
    util.to_screen(videoInfo['description'], '\n')

  def __searchVideo(self, search_term, numVideos):
    search = Search(api_key, search_term)
    vidList = []
    for i in range(numVideos):
      vidList.append(search.resultVideoInfo(i))
      util.to_screen('--',i+1,'--')
      self.__showVideoInfo(vidList[i])

    video_selected = False
    while not video_selected:
      video_num = int(input('Pick a video #: '))-1
      if 1 > video_num > 5:
        util.error_screen('Choose a number from the videos shown')
        continue
      video_selected = True

    return 'https://www.youtube.com/watch?v=' + vidList[video_num]['videoId']

  def search(self):
    search_term = ''
    if '-'+Download.OPTIONS['SEARCH_OPT'] in sys.argv:
      for arg in sys.argv[1:]:
        if arg[0] != '-':
          search_term = arg
          break
    else:
      return False
    if search_term == '':
      util.error_screen('Error - Search Term Not Found')
      exit()
    
    self.link = self.__searchVideo(search_term, 5)
    
    return True
  
  def audio(self):
    if '-'+Download.OPTIONS['AUDIO_OPT'] in sys.argv[1:]:
      self.media_type = Download.OPTIONS['AUDIO_OPT']
      return True
    return False

  def video(self):
    if '-'+Download.OPTIONS['VIDEO_OPT'] in sys.argv[1:]:
      self.media_type = Download.OPTIONS['VIDEO_OPT']
      return True
    return False


link = None
filename = None
media_type = Download.OPTIONS['AUDIO_OPT']

launch = Launchpad()
launch()