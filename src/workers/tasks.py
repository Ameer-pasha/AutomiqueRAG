import logging
import time


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.warning("Worker scaffold is idle until a durable queue adapter is configured.")
    while True:
        time.sleep(30)


if __name__ == "__main__":
    main()
