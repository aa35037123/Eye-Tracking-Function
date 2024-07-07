import requests
import os
import signal
import random
from multiprocessing import Pool
from pathlib import Path
from collect_links import CollectLinks

TOKEN = "6355462545:AAF7_X-9X3JQnfWp_kvpKQ3eqBmNwwsa8bc"
GROUP_CHAT_ID = '-4210499714'

def telegram_bot_sendtext(bot_message):
    send_text = (
        f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        f'?chat_id={GROUP_CHAT_ID}&parse_mode=Markdown&text={bot_message}'
    )

    response = requests.get(send_text)
    return response.json()

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
        if code == Sites.GOOGLE or Sites.GOOGLE_FULL:
            return "&tbs=itp:face"
        if code == Sites.NAVER or Sites.NAVER_FULL:
            return "&face=1"

def get_keywords(keywords_file='keywords.txt'):
        # read search keywords from file
        with open(keywords_file, 'r', encoding='utf-8-sig') as f:
            text = f.read()
            lines = text.split('\n')
            lines = filter(lambda x: x != '' and x is not None, lines)
            keywords = sorted(set(lines))

        print('{} keywords found: {}'.format(len(keywords), keywords))

        # re-save sorted keywords
        with open(keywords_file, 'w+', encoding='utf-8') as f:
            for keyword in keywords:
                f.write('{}\n'.format(keyword))

        return keywords

## For auto crawler
class AutoCrawler:
    def __init__(self, skip_already_exist=True, n_threads=4, do_google=True, do_naver=False, download_path='download',
                 full_resolution=False, face=False, no_gui=False, limit=5, proxy_list=None):
        """
        :param skip_already_exist: Skips keyword already downloaded before. This is needed when re-downloading.
        :param n_threads: Number of threads to download.
        :param do_google: Download from google.com (boolean)
        :param do_naver: Download from naver.com (boolean)
        :param download_path: Download folder path
        :param full_resolution: Download full resolution image instead of thumbnails (slow)
        :param face: Face search mode
        :param no_gui: No GUI mode. Acceleration for full_resolution mode.
        :param limit: Maximum count of images to download. (0: infinite)
        :param proxy_list: The proxy list. Every thread will randomly choose one from the list.
        """

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

        os.makedirs('./{}'.format(self.download_path), exist_ok=True)
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
        download_path='download'
        skip = True
        do_google = True
        # keywords = text
        os.makedirs('./{}'.format(download_path), exist_ok=True)

        tasks = []

        dir_name = '{}/{}'.format(download_path, keyword)
        google_done = False
        # naver_done = False
        full_resolution = False
        do_google = True
        do_naver = True
        n_threads=4

        # if google_done:
            # print('Skipping done task {}'.format(dir_name))
            # continue

        if do_google:
            if full_resolution:
                tasks.append([keyword, Sites.GOOGLE_FULL])
            else:
                tasks.append([keyword, Sites.GOOGLE])

        # if do_naver and not naver_done:
        #     if full_resolution:
        #         tasks.append([keyword, Sites.NAVER_FULL])
        #     else:
        #         tasks.append([keyword, Sites.NAVER])

        try:
            pool = Pool(n_threads, initializer=self.init_worker)
            pool.map(self.download, tasks)
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
        else:
            pool.terminate()
            pool.join()
        print('Task ended. Pool join.')

        # self.imbalance_check()

        print('End Program')


    if __name__ == '__main__':
        response = telegram_bot_sendtext("Hello, World")
        print(response)