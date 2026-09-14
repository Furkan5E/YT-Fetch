import config
import downloader
from cli import parse_args, apply_overrides
from batch import run_batch
from repl import run_repl


def main():
    args = parse_args()
    current_config = apply_overrides(config.load_config(), args)

    #non-interactive: a URL was passed directly, e.g. `yt-fetch <url>`
    if args.url:
        success = downloader.download_video(args.url, current_config)
        raise SystemExit(0 if success else 1)

    #non-interactive: --batch was passed, e.g. `yt-fetch --batch links.txt`
    if args.batch:
        success = run_batch(args.batch, current_config)
        raise SystemExit(0 if success else 1)

    #no CLI args: fall back to the interactive REPL
    run_repl(current_config)

if __name__ == "__main__":
    main()
