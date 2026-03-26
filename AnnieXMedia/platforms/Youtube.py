import os
import re
import json
import yt_dlp
import random
import logging
import aiohttp
import asyncio
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.aio import VideosSearch, Playlist
from AnnieXMedia.utils.database import is_on_off
from AnnieXMedia.utils.formatters import time_to_seconds
from AnnieXMedia import LOGGER

from config import API_URL, VIDEO_API_URL, API_KEY


def cookie_txt_file():
    """
    Deprecated: Cookies are no longer used. Using NextGen API instead.
    Returns None to force fallback to API-based methods.
    """
    # Always return None to use NextGen API
    return None


async def download_song(link: str, fast_mode: bool = True):
    video_id = link.split('v=')[-1].split('&')[0]

    download_folder = "downloads"
    for ext in ["mp3", "m4a", "webm"]:
        file_path = f"{download_folder}/{video_id}.{ext}"
        if os.path.exists(file_path):
            print(f"[FAST] Using cached audio: {file_path}")
            return file_path
    
    # Use NexGen API FIRST (fastest)
    if fast_mode:
        try:
            from AnnieXMedia.platforms.NextGenBots import get_nexgen_client
            client = get_nexgen_client()
            
            print(f"[FAST] Fetching audio from NexGen API: {video_id}")
            download_data = await client.get_song_download(video_id)
            
            print(f"[DEBUG] API Response: {download_data}")  # Debug log
            
            # Check for successful response (API returns dict with status/link)
            if download_data:
                # Try different possible response formats
                download_url = download_data.get("link") or download_data.get("url") or download_data.get("result", {}).get("link")
                file_format = download_data.get("format") or download_data.get("ext", "mp3")
                status = download_data.get("status", "")
                
                # If API returned a link directly or has status "done"/"success"
                if download_url and (status.lower() in ["done", "success"] or not status):
                    print(f"[FAST] Got audio URL from NexGen, downloading...")
                    file_extension = file_format.lower()
                    file_name = f"{video_id}.{file_extension}"
                    file_path = os.path.join(download_folder, file_name)
                    os.makedirs(download_folder, exist_ok=True)
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(download_url) as response:
                            with open(file_path, 'wb') as f:
                                while True:
                                    chunk = await response.content.read(16384)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                    print(f"[FAST] Audio download complete: {file_path}")
                    return file_path
        except Exception as e:
            print(f"[NexGenBots Audio Error] {e}")
            import traceback
            traceback.print_exc()
            print("[INFO] Falling back to alternative method...")
    
    # Use custom API if configured
    print(f"[FALLBACK] Using API_URL for audio...")
    if API_URL and API_KEY:
        song_url = f"{API_URL}/song/{video_id}?api={API_KEY}"
    else:
        print("[ERROR] No API configured!")
        return None
        
    async with aiohttp.ClientSession() as session:
        for attempt in range(10):
            try:
                async with session.get(song_url) as response:
                    if response.status != 200:
                        raise Exception(f"API request failed with status code {response.status}")
                
                    data = await response.json()
                    status = data.get("status", "").lower()

                    if status == "done":
                        download_url = data.get("link")
                        if not download_url:
                            raise Exception("API response did not provide a download URL.")
                        
                        file_format = data.get("format", "mp3")
                        file_extension = file_format.lower()
                        file_name = f"{video_id}.{file_extension}"
                        download_folder = "downloads"
                        os.makedirs(download_folder, exist_ok=True)
                        file_path = os.path.join(download_folder, file_name)

                        async with session.get(download_url) as file_response:
                            with open(file_path, 'wb') as f:
                                while True:
                                    chunk = await file_response.content.read(8192)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                        return file_path
                    elif status == "downloading":
                        print(f"[WAIT] API is still processing... (attempt {attempt + 1}/10)")
                        await asyncio.sleep(4)
                    else:
                        # Log detailed error info for debugging
                        error_msg = data.get("error") or data.get("message") or f"Unexpected status '{status}'"
                        print(f"[API ERROR] Status: {status}, Message: {error_msg}")
                        
                        # If it's a real error (not just processing), try fallback immediately
                        if status == "error":
                            print("[INFO] API reported error, will try alternative methods...")
                        
                        raise Exception(f"API error: {error_msg}")
            except Exception as e:
                print(f"[FAIL] {e}")
                return None
        else:
            print("⏱️ Max retries reached. Still downloading...")
            return None

async def download_video(link: str, fast_mode: bool = True):
    video_id = link.split('v=')[-1].split('&')[0]

    download_folder = "downloads"
    for ext in ["mp4", "webm", "mkv"]:
        file_path = f"{download_folder}/{video_id}.{ext}"
        if os.path.exists(file_path):
            print(f"[FAST] Using cached file: {file_path}")
            return file_path
    
    # Try NexGenBots API first (FAST MODE)
    if fast_mode:
        try:
            from AnnieXMedia.platforms.NextGenBots import get_nexgen_client
            client = get_nexgen_client()
            
            print(f"[FAST] Fetching from NexGen API: {video_id}")
            download_data = await client.get_video_download(video_id)
            
            print(f"[DEBUG] Video API Response: {download_data}")  # Debug log
            
            # Check for successful response
            if download_data:
                download_url = download_data.get("link") or download_data.get("url") or download_data.get("result", {}).get("link")
                file_format = download_data.get("format") or download_data.get("ext", "mp4")
                status = download_data.get("status", "")
                
                if download_url and (status.lower() in ["done", "success"] or not status):
                    print(f"[FAST] Got URL from NexGen, downloading...")
                    file_extension = file_format.lower()
                    file_name = f"{video_id}.{file_extension}"
                    file_path = os.path.join(download_folder, file_name)
                    os.makedirs(download_folder, exist_ok=True)
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(download_url) as response:
                            with open(file_path, 'wb') as f:
                                while True:
                                    chunk = await response.content.read(16384)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                    print(f"[FAST] Download complete: {file_path}")
                    return file_path
        except Exception as e:
            print(f"[NexGenBots Video Error] {e}")
            import traceback
            traceback.print_exc()
            print("[INFO] Falling back to alternative method...")
    
    # Fallback to custom API if configured
    print(f"[FALLBACK] Using VIDEO_API_URL fallback...")
    if VIDEO_API_URL and API_KEY:
        video_url = f"{VIDEO_API_URL}/video/{video_id}?api={API_KEY}"
    else:
        print("[ERROR] No API configured!")
        return None
        
    async with aiohttp.ClientSession() as session:
        for attempt in range(10):
            try:
                async with session.get(video_url) as response:
                    if response.status != 200:
                        raise Exception(f"API request failed with status code {response.status}")
                
                    data = await response.json()
                    status = data.get("status", "").lower()

                    if status == "done":
                        download_url = data.get("link")
                        if not download_url:
                            raise Exception("API response did not provide a download URL.")
                        
                        file_format = data.get("format", "mp4")
                        file_extension = file_format.lower()
                        file_name = f"{video_id}.{file_extension}"
                        download_folder = "downloads"
                        os.makedirs(download_folder, exist_ok=True)
                        file_path = os.path.join(download_folder, file_name)

                        async with session.get(download_url) as file_response:
                            with open(file_path, 'wb') as f:
                                while True:
                                    chunk = await file_response.content.read(8192)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                        return file_path
                    elif status == "downloading":
                        await asyncio.sleep(8)
                    else:
                        error_msg = data.get("error") or data.get("message") or f"Unexpected status '{status}'"
                        raise Exception(f"API error: {error_msg}")
            except Exception as e:
                print(f"[FAIL] {e}")
                return None
        else:
            print("⏱️ Max retries reached. Still downloading...")
            return None

async def check_file_size(link):
    """
    Check file size using NexGen API instead of cookies
    Returns file size in bytes or None if unavailable
    """
    try:
        # Extract video ID from link
        video_id = link.split('v=')[-1].split('&')[0]
        
        # Use NexGen API to get download info (includes size)
        from AnnieXMedia.platforms.NextGenBots import get_nexgen_client
        client = get_nexgen_client()
        
        download_data = await client.get_song_download(video_id)
        
        if download_data:
            # Try to get file size from API response
            file_size = download_data.get("filesize") or download_data.get("size")
            if file_size:
                print(f"[INFO] File size from API: {file_size} bytes")
                return int(file_size)
                
        print("[INFO] File size not available from API")
        return None
        
    except Exception as e:
        print(f"[ERROR] Failed to check file size: {e}")
        return None

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        umm = text[offset : offset + length]
        if "?si=" in umm:
            umm = umm.split("?si=")[0]
        return umm

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        # Try NexGenBots API first for direct download
        try:
            from AnnieXMedia.platforms.NextGenBots import get_nexgen_client
            client = get_nexgen_client()
            
            # Extract video ID
            video_id = link.split('v=')[-1].split('&')[0]
            download_data = await client.get_video_download(video_id)
            
            if download_data and download_data.get("status") == "done":
                download_url = download_data.get("link")
                if download_url:
                    LOGGER(__name__).info(f"Using NexGenBots API for video: {video_id}")
                    return 1, download_url
        except Exception as e:
            LOGGER(__name__).error(f"NexGenBots video API failed: {e}")
        
        # Try video API fallback
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
        except Exception as e:
            print(f"Video API failed: {e}")
        
        # Fallback to cookies
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return 0, "No cookies found. Cannot download video."
            
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_file,
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        try:
            plist = await Playlist.get(link)
        except:
            return []

        videos = plist.get("videos") or []
        ids: list[str] = []
        for data in videos[:limit]:
            if not data:
                continue
            vid = data.get("id")
            if not vid:
                continue
            ids.append(vid)
        return ids

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return [], link
            
        ytdl_opts = {"quiet": True, "cookiefile" : cookie_file}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()
        def audio_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download audio.")
                
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile" : cookie_file,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download video.")
                
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile" : cookie_file,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download song video.")
                
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile" : cookie_file,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download song audio.")
                
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile" : cookie_file,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            await download_song(link)
            fpath = f"downloads/{link}.mp3"
            return fpath
        elif songaudio:
            await download_song(link)
            fpath = f"downloads/{link}.mp3"
            return fpath
        elif video:
            # Try video API first
            try:
                downloaded_file = await download_video(link)
                if downloaded_file:
                    direct = True
                    return downloaded_file, direct
            except Exception as e:
                print(f"Video API failed: {e}")
            
            # Fallback to cookies
            cookie_file = cookie_txt_file()
            if not cookie_file:
                print("No cookies found. Cannot download video.")
                return None, None
                
            if await is_on_off(1):
                direct = True
                downloaded_file = await download_song(link)
            else:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    "--cookies", cookie_file,
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    f"{link}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = False
                else:
                   file_size = await check_file_size(link)
                   if not file_size:
                     print("None file Size")
                     return None, None
                   total_size_mb = file_size / (1024 * 1024)
                   if total_size_mb > 250:
                     print(f"File size {total_size_mb:.2f} MB exceeds the 100MB limit.")
                     return None, None
                   direct = True
                   downloaded_file = await loop.run_in_executor(None, video_dl)
        else:
            direct = True
            downloaded_file = await download_song(link)
        return downloaded_file, direct