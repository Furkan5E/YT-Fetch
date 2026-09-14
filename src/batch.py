import os

import downloader


def run_batch(batch_file, current_config):
    """Downloads every link in batch_file. Returns True if all succeeded."""
    if not os.path.exists(batch_file):
        print(f"\n[Error] {batch_file} not found. Please create it and add links.")
        return False

    with open(batch_file, "r") as f:
        links = [line.strip() for line in f if line.strip()]

    if not links:
        print(f"\n[Error] {batch_file} is empty.")
        return False

    print(f"\nFound {len(links)} links in {batch_file}. Starting batch process...")
    succeeded = 0
    failed_links = []
    for link in links:
        if downloader.download_video(link, current_config):
            succeeded += 1
        else:
            failed_links.append(link)
    print(f"\nBatch processing complete! {succeeded}/{len(links)} succeeded.")
    if failed_links:
        print("Failed links:")
        for link in failed_links:
            print(f"  - {link}")
    return not failed_links
