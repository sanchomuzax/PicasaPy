"""Entry point for packaged macOS PicasaPy application (#3021 / macOS port).

PyInstaller runs entry point scripts directly without module context.
This launcher avoids relative imports and handles background worker dispatch.
"""

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--picasapy-video-decode":
        if len(sys.argv) != 4:
            sys.exit(2)
        from picasapy.thumbs.video_decode_worker import main as worker_main

        sys.exit(worker_main(sys.argv[2], sys.argv[3]))

    if len(sys.argv) > 1 and sys.argv[1] == "--picasapy-poster":
        from picasapy.printing.poster_worker import main as worker_main

        sys.exit(worker_main(sys.argv[2:]))

    from picasapy.app.__main__ import main

    sys.exit(main())
