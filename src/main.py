import argparse
import config
import downloader
import os

def parse_args():
    parser = argparse.ArgumentParser(
        prog="yt-fetch",
        description="Interactive and scriptable YouTube downloader."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="A video URL to download once, non-interactively, then exit."
    )
    parser.add_argument(
        "--batch",
        nargs="?",
        const="batch.txt",
        default=None,
        metavar="FILE",
        help="Download every link in FILE (default: batch.txt), then exit."
    )
    return parser.parse_args()

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

def handle_config_command(parts, current_config):
    """Parses and executes .config commands."""
    #case 1: ".config" -> print entire config
    if len(parts) == 1:
        print("\nCurrent Configuration:")
        for k, v in current_config.items():
            print(f"  {k} = {v}")
            
    #case 2: ".config key" -> print specific key
    elif len(parts) == 2:
        key = parts[1].lower()
        if key in current_config:
            print(f"{current_config[key]}")
        else:
            print(f"Unknown config key: '{key}'")
            
    #case 3: ".config key value" -> update key
    elif len(parts) >= 3:
        key = parts[1].lower()
        value = " ".join(parts[2:])
        #preserve casing for paths
        if key not in config.CASE_SENSITIVE_KEYS:
            value = value.lower()
        
        if key in current_config:
            success = config.validate_and_update(current_config, key, value)
            if success:
                if key == "quality":
                    print(f"quality is set to {value}kbs")
                else:
                    print(f"{key} is set to {value}")
        else:
            print(f"Unknown config key: '{key}'. Valid keys are: {', '.join(current_config.keys())}")


def main():
    args = parse_args()
    current_config = config.load_config()
    #yt-fetch <url>
    if args.url:
        success = downloader.download_video(args.url, current_config)
        raise SystemExit(0 if success else 1)
    #yt-fetch --batch links.txt
    if args.batch:
        success = run_batch(args.batch, current_config)
        raise SystemExit(0 if success else 1)

    print("YT Fetch")
    while True:
        try:
            user_input = input("\nEnter Link: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not user_input:
            continue

        #command: quit
        if user_input.lower() == 'quit':
            print("Terminating application.")
            break
            
        #command: batch
        elif user_input.lower() == 'batch':
            run_batch("batch.txt", current_config)
                
        # Command: Config
        elif user_input.lower().startswith('.config'):
            parts = user_input.split()
            handle_config_command(parts, current_config)
                    
        #link entered, download
        else:
            downloader.download_video(user_input, current_config)

if __name__ == "__main__":
    main()