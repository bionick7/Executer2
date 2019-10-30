# -*- coding: UTF-8 -*-

import datetime
import pymongo
import traceback

from program_base import get_globals, set_globals
import message_processing
import response_functions
import cah_functions

from time import sleep as wait


def run():
    # define the functions
    response_functions.run()
    cah_functions.run()
    # run the bot
    message_processing.run()


def main():
    logger = get_globals("logger")
    url = get_globals("auth|database login url")
    logger.indicate_process_start("Connecting to Database ...")
    try:
        cl = pymongo.MongoClient(url)
        set_globals(database_client=cl)
    except pymongo.errors.ConfigurationError as e:
        logger.indicate_process_outcome("\nAn error occurred while trying to setup the database client."
                                        " See stderr for more information")
        logger.log_traceback()
        return -1
    else:
        logger.indicate_process_outcome("Success")
    start = datetime.datetime.now()
    try:
        run()
    except Exception as e:
        time_display_format = get_globals("general|time display template")
        logger.log_line("-----------------")
        logger.log_line(f"An error of type {type(e)} occurred at"
                        f" {datetime.datetime.now().strftime(time_display_format)}")
        logger.log_line(f"Bot run for {(datetime.datetime.now() - start).seconds}s. See stderr for more information")
        logger.log_traceback()
        return 1


if __name__ == "__main__":
    while 1:
        exit_code = main()
        if exit_code == -1:
            break
        elif exit_code == 0:
            continue
        elif exit_code == 1:
            wait(1)
        else:
            print(f"Exit code {exit_code} not known")
