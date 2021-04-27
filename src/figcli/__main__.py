# -*- coding: utf-8 -*-
import multiprocessing

"""bootstrap.__main__: executed when bootstrap directory is called as script."""

from figcli.entrypoint import cli

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        cli.main()
    except Warning:
        pass