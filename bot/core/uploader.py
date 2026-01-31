import os
import shutil
import asyncio

from pathlib import Path
from bot import Config
from bot.utils.message import send_audio, send_document
from ..models.uploader import Uploader
from ..settings import bot_settings
from ..utils.zip import ZipHandler


class RcloneUploader(Uploader):
    @classmethod
    async def upload(cls, task_details, filepath, metadata):
        if ZipHandler.should_zip(metadata):
            zip_file = ZipHandler.get_zip_name(metadata)
            await ZipHandler.create_zip(filepath, zip_file)
        
        await cls._rclone_upload(task_details.dl_folder)
    

    @staticmethod
    async def _rclone_upload(local_path: Path):
        cmd = f'rclone copy --config ./rclone.conf "{str(local_path)}" "{Config.RCLONE_DEST}"'
        task = await asyncio.create_subprocess_shell(cmd)
        await task.wait()




class TelegramUploader(Uploader):
    @classmethod
    async def upload(cls, task_details, filepath, metadata):
        caption = metadata.title
        if ZipHandler.should_zip(metadata):
            zip_name = ZipHandler.get_zip_name(metadata)
            zip_files = await ZipHandler.create_zip(filepath, zip_name, True)
            for z in zip_files:
                await send_document(z, task_details, caption=caption)
                z.unlink()
        else:
            await send_audio(filepath, metadata, task_details, caption=caption)


class LocalUploader:
    @classmethod
    async def upload(cls, task_details, filepath, metadata):
        if ZipHandler.should_zip(metadata):
            zip_file = ZipHandler.get_zip_name(metadata)
            await ZipHandler.create_zip(filepath, zip_file)
        
        source = task_details.dl_folder
        destination = Config.LOCAL_STORAGE
        destination.mkdir(parents=True, exist_ok=True)
        for item in source.iterdir():
            dest_path = destination / item.name
            if item.is_dir():
                for root, dirs, files in os.walk(item):
                    root = Path(root)
                    rel_path = root.relative_to(item)
                    dest_subdir = dest_path / rel_path
                    dest_subdir.mkdir(parents=True, exist_ok=True)
                    for file in files:
                        src_file = root / file
                        dest_file = dest_subdir / file
                        # overwrite if exists
                        if dest_file.exists():
                            dest_file.unlink()
                        await asyncio.to_thread(shutil.move, str(src_file), str(dest_file))
                await asyncio.to_thread(shutil.rmtree, item, True)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                if dest_path.exists():
                    dest_path.unlink()
                await asyncio.to_thread(shutil.move, str(item), str(dest_path))


def get_uploader() -> type[Uploader]:
    uploaders = {
        'rclone': RcloneUploader,
        'telegram': TelegramUploader,
        'local': LocalUploader,
    }
    return uploaders.get(bot_settings.upload_mode.value.lower(), TelegramUploader)