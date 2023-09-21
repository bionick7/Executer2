# -*- coding: UTF-8 -*-
import datetime

from time import sleep as wait


def main():
    import message_processing
    logger = message_processing.logger
    start = datetime.datetime.now()
    try:
        message_processing.run()
    except Exception as e:
        time_display_format = message_processing.data["config"]["time display template"]
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
