import config
import downloader
import os

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
        if key not in ['ffmpeg_path', 'output_dir']:
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
    current_config = config.load_config()
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
            if os.path.exists("batch.txt"):
                with open("batch.txt", "r") as f:
                    links = [line.strip() for line in f if line.strip()]
                
                if not links:
                    print("\n[Error] batch.txt is empty.")
                else:
                    print(f"\nFound {len(links)} links in batch.txt. Starting batch process...")
                    for link in links:
                        downloader.download_video(link, current_config)
                    print("\nBatch processing complete!")
            else:
                print("\n[Error] batch.txt not found. Please create it in the same folder and add links.")
                
        # Command: Config
        elif user_input.lower().startswith('.config'):
            parts = user_input.split()
            handle_config_command(parts, current_config)
                    
        #link entered, download
        else:
            downloader.download_video(user_input, current_config)

if __name__ == "__main__":
    main()