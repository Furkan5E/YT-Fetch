import os

from . import config
from . import downloader

BATCH_FILE_HEADER = (
    "# Add one link per line, then run `batch` in yt-fetch (or `yt-fetch --batch`).\n"
    "# Lines starting with # are ignored.\n"
)


def run_batch(batch_file, current_config):
    """Downloads every link in batch_file. Returns True if all succeeded."""
    if not os.path.exists(batch_file):
        #only the default file is created; a missing custom path is more likely a typo
        if os.path.abspath(batch_file) == os.path.abspath(config.get_batch_file()):
            with open(batch_file, "w") as f:
                f.write(BATCH_FILE_HEADER)
            print(f"\nCreated {batch_file}. Add links to it (one per line) and run batch again.")
        else:
            print(f"\n[Error] {batch_file} not found. Please create it and add links.")
        return False

    with open(batch_file, "r") as f:
        links = [line.strip() for line in f]
    #only whole-line comments are skipped, since URLs can contain '#'
    links = [link for link in links if link and not link.startswith("#")]

    if not links:
        print(f"\n[Error] {batch_file} has no links.")
        return False

    print(f"\nFound {len(links)} links in {batch_file}. Starting batch process...")
    succeeded = 0
    failed_links = []
    try:
        for link in links:
            if downloader.download_video(link, current_config):
                succeeded += 1
            else:
                failed_links.append(link)
    except KeyboardInterrupt:
        #the interrupted link counts as not attempted
        skipped = len(links) - succeeded - len(failed_links)
        print(f"\nBatch cancelled. {succeeded}/{len(links)} succeeded, {skipped} not downloaded.")
        raise
    print(f"\nBatch processing complete! {succeeded}/{len(links)} succeeded.")
    if failed_links:
        print("Failed links:")
        for link in failed_links:
            print(f"  - {link}")
    return not failed_links
