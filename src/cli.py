import argparse

import config

#config keys that can be overridden with CLI flags
OVERRIDABLE_KEYS = [
    "type", "quality", "resolution", "metadata",
    "allow_playlists", "remove_sponsors", "embed_lyrics"
]

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
    batch_file = config.get_batch_file()
    parser.add_argument(
        "--batch",
        nargs="?",
        const=batch_file,
        default=None,
        metavar="FILE",
        help=f"Download every link in FILE (default: {batch_file}), then exit."
    )
    for key in OVERRIDABLE_KEYS:
        flag = "--" + key.replace("_", "-")
        parser.add_argument(
            flag,
            choices=config.VALID_OPTIONS.get(key),
            default=None,
            help=f"Override '{key}' for this run only (config.txt is left unchanged)."
        )
    parser.add_argument(
        "--output-dir",
        default=None,
        metavar="PATH",
        help="Override 'output_dir' for this run only (config.txt is left unchanged)."
    )
    return parser.parse_args()

def apply_overrides(current_config, args):
    """Returns a copy of current_config with any passed CLI flags applied
    on top. The underlying config.txt is never touched by this."""
    overrides = {key: getattr(args, key) for key in OVERRIDABLE_KEYS if getattr(args, key) is not None}
    if args.output_dir is not None:
        overrides["output_dir"] = args.output_dir
    return {**current_config, **overrides} if overrides else current_config