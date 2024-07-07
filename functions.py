import requests
import os
import signal
import random
from youtubesearchpython import VideosSearch, Transcript    # Consider the following repo: https://github.com/alexmercerind/youtube-search-python/tree/main
from multiprocessing import Pool
from pathlib import Path
from collect_links import CollectLinks
import shutil
import base64
# import pafy     # Many, many errors due to yt_dl
from pytube import YouTube
import vlc
import time
from googleapiclient.discovery import build

TOKEN = "6355462545:AAF7_X-9X3JQnfWp_kvpKQ3eqBmNwwsa8bc"
GROUP_CHAT_ID = '-4210499714'
YOUTUBE_API_KEY = 'AIzaSyArA5OuSiFF-8gGtlBnPgpufn8hcxR5el0'

def telegram_bot_sendtext(bot_message):
    send_text = (
        f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        f'?chat_id={GROUP_CHAT_ID}&parse_mode=Markdown&text={bot_message}'
    )

    response = requests.get(send_text)
    return response.json()


"""
## Music
"""

def yt_search_video(title):
    """ Search Youtube video with the title given.

    Args:
        title (str): The title of video

    Returns:
        A tuple contain the following elements:
            (1) Dict: A Dict contain only the first resulting video's info
                * If the search failed, it will return a null Dict.
            (2) bool: A flag indicate that if the search succeeded.
    """
    try:
        videosSearch = VideosSearch(title, limit = 1)
        print(f"Playing {title}.")
        return (videosSearch.result()['result'][0], 1)
    except Exception:
        print(f"Search failed when searching {title}.")
        return ({}, 0)   # Null Dict

def yt_play_video(video_info):
    """ Play video with VLC Media Player

    Args:
        video_info (dict): The info of the video (From yt_search_video())
    """
    url = video_info['link']
    video = pafy.new(url)
    best = video.getbest()
    playurl = best.url
    Instance = vlc.Instance()
    player = Instance.media_player_new()
    Media = Instance.media_new(playurl)
    Media.get_mrl()
    player.set_media(Media)
    
    # Start playing video.
    if player.play() == 0:   # Successful play
        # You can add a while not player.is_playing() loop if your computer or net (or both) is(are) slow as fucked.
        time.sleep(10)   # Hard coded delay to ensure vlc has been established
        while player.is_playing():
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
        print("Video end")
        # player.stop()     # It brings about an error message, and IDK why.
    else:   # Failed playing
        print("Failed to play the video")

def yt_play_video_with_transcript(video_info):
    """ Play video with VLC Media Player (With transcript version)

    Args:
        video_info (dict): The info of the video (From yt_search_video())
    """
    url = video_info['link']
    video = pafy.new(url)
    best = video.getbest()
    playurl = best.url
    Instance = vlc.Instance()
    player = Instance.media_player_new()
    Media = Instance.media_new(playurl)
    Media.get_mrl()
    player.set_media(Media)
    transcript = Transcript.get(url)['segments']
    transcript_len = len(transcript)
    
    # Start playing video.
    subscript = ""
    i = 0
    if player.play() == 0:   # Successful play
        time.sleep(5)
        print("----------------- Start subscript ---------------------")
        while player.is_playing():
            try:
                cur_time = player.get_time()     # In ms
                if cur_time > 20000: break
                if i < transcript_len and cur_time >= int(transcript[i]['startMs']):
                    subscript = transcript[i]['text']
                    print(subscript)
                    i += 1
                time.sleep(0.1)
            except KeyboardInterrupt:
                break
        print("----------------- End subscript ---------------------")
        print("Video end")
        # player.stop()
    else:   # Failed playing
        print("Failed to play the video")
        
def play_music(title="Never Gonna Give You Up"):
    # You can change it to whatever you like.
    video_info, status = yt_search_video(title)
    yt_play_video_with_subtitle(video_info)
    

class Sites:
    GOOGLE = 1
    NAVER = 2
    GOOGLE_FULL = 3
    NAVER_FULL = 4

    @staticmethod
    def get_text(code):
        if code == Sites.GOOGLE:
            return 'google'
        elif code == Sites.NAVER:
            return 'naver'
        elif code == Sites.GOOGLE_FULL:
            return 'google'
        elif code == Sites.NAVER_FULL:
            return 'naver'

    @staticmethod
    def get_face_url(code):
        if code == Sites.GOOGLE or code == Sites.GOOGLE_FULL:
            return "&tbs=itp:face"
        if code == Sites.NAVER or code == Sites.NAVER_FULL:
            return "&face=1"

class AutoCrawler:
    def __init__(self, skip_already_exist=True, n_threads=4, do_google=True, do_naver=False, download_path='download',
                 full_resolution=False, face=False, no_gui=False, limit=5, proxy_list=None):
        self.skip = skip_already_exist
        self.n_threads = n_threads
        self.do_google = do_google
        self.do_naver = do_naver
        self.download_path = download_path
        self.full_resolution = full_resolution
        self.face = face
        self.no_gui = no_gui
        self.limit = limit
        self.proxy_list = proxy_list if proxy_list and len(proxy_list) > 0 else None

        os.makedirs(self.download_path, exist_ok=True)

    @staticmethod
    def make_dir(dirname):
        current_path = os.getcwd()
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path):
            os.makedirs(path)
    
    @staticmethod
    def save_object_to_file(object, file_path, is_base64=False):
        try:
            with open('{}'.format(file_path), 'wb') as file:
                if is_base64:
                    file.write(object)
                else:
                    shutil.copyfileobj(object.raw, file)
        except Exception as e:
            print('Save failed - {}'.format(e))

    @staticmethod
    def base64_to_object(src):
        header, encoded = str(src).split(',', 1)
        data = base64.decodebytes(bytes(encoded, encoding='utf-8'))
        return data
    
    def init_worker(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def download(self, args):
        self.download_from_site(keyword=args[0], site_code=args[1])

    def download_images(self, keyword, links, site_name, max_count=0):
        self.make_dir('{}/{}'.format(self.download_path, keyword.replace('"', '')))
        total = len(links)
        success_count = 0

        if max_count == 0:
            max_count = total

        for index, link in enumerate(links):
            if success_count > max_count:
                break

            try:
                print('Downloading {} from {}: {} / {}'.format(keyword, site_name, success_count + 1, max_count))

                if str(link).startswith('data:image/jpeg;base64'):
                    response = self.base64_to_object(link)
                    ext = 'jpg'
                    is_base64 = True
                elif str(link).startswith('data:image/png;base64'):
                    response = self.base64_to_object(link)
                    ext = 'png'
                    is_base64 = True
                else:
                    response = requests.get(link, stream=True, timeout=10)
                    ext = self.get_extension_from_link(link)
                    is_base64 = False

                no_ext_path = '{}/{}/{}_{}'.format(self.download_path.replace('"', ''), keyword, site_name,
                                                   str(index).zfill(4))
                path = no_ext_path + '.' + ext
                self.save_object_to_file(response, path, is_base64=is_base64)

                success_count += 1
                del response

                ext2 = self.validate_image(path)
                if ext2 is None:
                    print('Unreadable file - {}'.format(link))
                    os.remove(path)
                    success_count -= 1
                else:
                    if ext != ext2:
                        path2 = no_ext_path + '.' + ext2
                        os.rename(path, path2)
                        print('Renamed extension {} -> {}'.format(ext, ext2))

            except KeyboardInterrupt:
                break
            except Exception as e:
                print('Download failed - ', e)
                continue

    def download_from_site(self, keyword, site_code):
        site_name = Sites.get_text(site_code)
        add_url = Sites.get_face_url(site_code) if self.face else ""

        try:
            proxy = None
            if self.proxy_list:
                proxy = random.choice(self.proxy_list)
            collect = CollectLinks(no_gui=self.no_gui, proxy=proxy)  # initialize chrome driver
        except Exception as e:
            print('Error occurred while initializing chromedriver - {}'.format(e))
            return

        try:
            print('Collecting links... {} from {}'.format(keyword, site_name))

            if site_code == Sites.GOOGLE:
                links = collect.google(keyword, add_url)

            elif site_code == Sites.NAVER:
                links = collect.naver(keyword, add_url)

            elif site_code == Sites.GOOGLE_FULL:
                links = collect.google_full(keyword, add_url, self.limit)

            elif site_code == Sites.NAVER_FULL:
                links = collect.naver_full(keyword, add_url)

            else:
                print('Invalid Site Code')
                links = []

            print('Downloading images from collected links... {} from {}'.format(keyword, site_name))
            self.download_images(keyword, links, site_name, max_count=self.limit)
            Path('{}/{}/{}_done'.format(self.download_path, keyword.replace('"', ''), site_name)).touch()

            print('Done {} : {}'.format(site_name, keyword))

        except Exception as e:
            print('Exception {}:{} - {}'.format(site_name, keyword, e))
            return

    def do_crawling(self, keyword):
        tasks = []

        dir_name = '{}/{}'.format(self.download_path, keyword)
        # google_done = os.path.exists(os.path.join(os.getcwd(), dir_name, 'google_done'))
        # naver_done = os.path.exists(os.path.join(os.getcwd(), dir_name, 'naver_done'))
        # if google_done and self.skip:
        #     print('Skipping done task {}'.format(dir_name))

        if self.do_google:
            if self.full_resolution:
                tasks.append([keyword, Sites.GOOGLE_FULL])
            else:
                tasks.append([keyword, Sites.GOOGLE])

        print(f'task: {tasks}')
        try:
            pool = Pool(self.n_threads, initializer=self.init_worker)
            pool.map(self.download, tasks)
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
        else:
            pool.terminate()
            pool.join()
        print('Task ended. Pool join.')

        print('End Program')

    if __name__ == '__main__':
        # response = telegram_bot_sendtext("Hello, World")
        # print(response)
        play_music()