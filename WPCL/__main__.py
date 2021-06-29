import argparse
import logging
import sys

from WPCL import WPCL


def main():
    parser = argparse.ArgumentParser(
        prog="WPCL",
        description="Wireless PC Lock - Copyright (C) 2020 Zack Didcott",
    )
    parser.add_argument(
        "-d",
        "--device",
        type=str,
        default="HID 13b7:7417",
        help="specify a device name (default: HID 13b7:7417)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=5,
        help=(
            "timeout before locking, in seconds; should be longer than the "
            "interval between communications (default: 5)"
        ),
    )
    parser.add_argument(
        "-l", "--log", type=str, default=None, help="output log into a file"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=-1,
        default=0,
        dest="verbosity",
        help="only display errors",
    )
    group.add_argument(
        "-v",
        "--verbose",
        action="store_const",  # See also: action="count"
        const=1,
        default=0,
        dest="verbosity",
        help="display debugging information (default: INFO)",
    )

    args = parser.parse_args()

    # Logging #
    loglevel = 20 - (args.verbosity * 10)
    logging.basicConfig(
        level=loglevel,
        filename=args.log,
        format="%(asctime)s | [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    logging.info(parser.description)
    logging.debug("== Configuration ==")
    for arg, value in sorted(vars(args).items()):
        logging.debug(f"{arg.title()}: {value}")
    logging.debug("===================")

    app = WPCL(args.device, args.timeout)
    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
