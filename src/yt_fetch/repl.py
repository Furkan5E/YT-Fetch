from . import config, get_version
from . import downloader
from .batch import run_batch


def handle_config_command(parts, current_config, saved_config):
    """Parses and executes .config commands. Updates are written to
    saved_config (config.toml) so CLI overrides in current_config never get saved."""
    #".config reset" / ".config reset key" -> restore defaults
    if len(parts) >= 2 and parts[1].lower() == 'reset':
        key = parts[2].lower() if len(parts) > 2 else None
        reset_keys = config.reset_config(saved_config, key)
        if reset_keys is None:
            print(f"Unknown config key: '{key}'")
            return
        for k in reset_keys:
            current_config[k] = saved_config[k]
        if key is None:
            print("All settings reset to defaults.")
        else:
            print(f"{key} reset to {config.format_value(saved_config[key])}")

    #case 1: ".config" -> print entire config
    elif len(parts) == 1:
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

COMMANDS = [
    ("<URL or search>", "Download the link, or the top YouTube result for a search"),
    ("batch", "Download every link in batch.txt (lines starting with # are skipped)"),
    (".config", "Show all settings and where config.toml is"),
    (".config KEY", "Show one setting"),
    (".config KEY VALUE", "Change a setting and save it"),
    (".config reset [KEY]", "Reset one setting, or all of them, to the default"),
    ("help", "Show this help"),
    ("quit", "Exit (Ctrl+C at this prompt also exits)"),
]

def print_help():
    print("\nCommands:")
    for command, description in COMMANDS:
        print(f"  {command:<21}{description}")
    print("\nCtrl+C during a download cancels it and removes its partial files.")
    print(f"batch.txt: {config.get_batch_file()}")

    print("\nSettings (change with .config KEY VALUE):")
    for key, description in config.KEY_DESCRIPTIONS.items():
        print(f"  {key:<21}{description}")

def run_repl(current_config, saved_config):
    """Runs the interactive Enter Link / .config / batch / help / quit loop."""
    print(f"YT Fetch {get_version()}. Type 'help' for commands.")
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

        #Ctrl+C here cancels the current command and returns to the prompt;
        #download_video/run_batch have already reported it
        try:
            #command: help
            if user_input.lower() in ('help', '?'):
                print_help()

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
        except KeyboardInterrupt:
            pass