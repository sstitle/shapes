
import coloredlogs, logging

def main():
    logger = logging.getLogger(__name__)
    coloredlogs.install(level='DEBUG', logger=logger)
    logger.info("Hello, World!")

if __name__ == "__main__":
    main()
