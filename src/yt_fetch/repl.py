from . import config
from . import downloader
from .batch import run_batch


def handle_config_command(parts, current_config, saved_config):
    """Parses and executes .config commands. Updates are written to
    saved_config (config.toml) so CLI overrides in current_config never get saved."""
    #case 1: ".config" -> print entire config
    if len(parts) == 1:
        print("\nCurrent Configuration:")
        for k, v in current_config.items():
            print(f"  {k} = {config.format_value(v)}")
        print(f"\nConfig file: {config.get_config_file()}")

    #case 2: ".config key" -> print specific key
    elif len(parts) == 2:
        key = parts[1].lower()
        if key in current_config:
            print(config.format_value(current_config[key]))
        else:
            print(f"Unknown config key: '{key}'")

    #case 3: ".config key value" -> update key
    elif len(parts) >= 3:
        key = parts[1].lower()
        value = config.parse_value(key, " ".join(parts[2:]))

        if key in current_config:
            success = config.validate_and_update(saved_config, key, value)
            if success:
                current_config[key] = value
                if key == "quality":
                    print(f"quality is set to {value}kbs")
                else:
                    print(f"{key} is set to {config.format_value(value)}")
        else:
            print(f"Unknown config key: '{key}'. Valid keys are: {', '.join(current_config.keys())}")

def run_repl(current_config, saved_config):
    """Runs the interactive Enter Link / .config / batch / quit loop."""
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
            run_batch(config.get_batch_file(), current_config)

        # Command: Config
        elif user_input.lower().startswith('.config'):
            parts = user_input.split()
            handle_config_command(parts, current_config, saved_config)

        #link entered, download
        else:
            downloader.download_video(user_input, current_config)