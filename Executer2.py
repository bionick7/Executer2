# -*- coding: UTF-8 -*-

import datetime
import pymongo, pymongo.errors
#import dns

from program_base import get_globals, set_globals
import message_processing
import function_library
import cah_functions

from time import sleep as wait


def run():
    # define the functions
    function_library.run()
    cah_functions.run()
    # run the bot
    message_processing.run()


def main():
    logger = get_globals("logger")
    url = get_globals("auth|database login url")
    logger.indicate_process_start("Connecting to Database ...")
    try:
        cl = pymongo.MongoClient(url)
        # To test, if it can actually fetch data
        _ = cl["executer_database"]["servers"].find()[0]
    except (pymongo.errors.ConfigurationError, pymongo.errors.OperationFailure):
        logger.indicate_process_outcome("\nAn error occurred while trying to setup the database client."
                                        " See stderr for more information")
        logger.log_traceback()
        set_globals(database_access=False)
    else:
        set_globals(database_client=cl)
        logger.indicate_process_outcome("Success")
        set_globals(database_access=True)
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
        logger.log_line("=" * 100)
        return 1
    return -1


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
