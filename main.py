import argparse
import logging
import logging.config
import os
import sys
import json
import docker
import yaml

from keys.telegram import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN

logging_yaml_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "resources", "logging_config.yaml")
)

# https://docker-py.readthedocs.io/en/stable/
client = docker.from_env()

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--container", help="Container to check for new image", required=True)
parser.add_argument("-u", "--update", help="Set to perform automatic update", required=False, action='store_true')
parser.add_argument("-t", "--tag", help="Defines the new version which should be used. Default=latest", required=False, default="latest")
parser.add_argument("-e", "--envfile", help="ENV file for docker arguments to pass to docker run. See docker-env.example", nargs='?', type=argparse.FileType('r'), required=False)
args = parser.parse_args()


def setup_logging():
    with open(logging_yaml_path, "r") as f:
        config = yaml.safe_load(f.read())
        config["handlers"]["telegram"]["token"] = TELEGRAM_TOKEN
        config["handlers"]["telegram"]["chat_id"] = TELEGRAM_CHAT_ID
        logging.config.dictConfig(config)


def get_image_tag(container):
    logger.debug("Image of container: {}".format(container.image))
    return container.image.tags[0]


def pull_image(container, tag='latest'):
    container_image = get_image_tag(container)
    logger.debug("Try to find new image for {} and tag {}".format(container_image, tag))
    image_name = container_image.split(':')[0]
    return client.images.pull(image_name, tag=tag)


def get_container(name):
    try:
        return client.containers.get(name)
    except Exception as err:
        logger.error("Container not found. Error: {}".format(err))
        sys.exit(1)


def compare(image, container):
    return image.id == container.image.id


def autoupdate(container, tag='latest', arguments={}):
    image_name = get_image_tag(container).split(':')[0]
    container.stop()
    container.remove()
    return client.containers.run(image_name+":"+tag, detach=True, name=container.name, **arguments)


def parse_envfile(envfile):
    if envfile:
        return json.load(envfile)
    else:
        return {}


if __name__ == '__main__':
    setup_logging()
    logger = logging.getLogger(__name__)

    container_name = args.container
    logger.debug("Going to check container {}".format(container_name))

    container = get_container(container_name)
    image = pull_image(container, args.tag)
    logger.debug("Image version:      {}".format(image.id))

    if compare(image, container):
        logger.debug("Container {} still up-to-date".format(container.name))
    else:
        if args.update:
            logger.info("Container {} outdated. Try to perform auto-update.".format(container_name))
            try:
                arguments = parse_envfile(args.envfile)
                newcontainer = autoupdate(container, args.tag, arguments)
                logger.info("Container {} updated. Now running on {}.".format(newcontainer.name, newcontainer.image.tags))
            except Exception as err:
                logging.error("Error updating container {}. Error: {}".format(container_name, err))
                sys.exit(1)
        else:
            logger.warning("Container {} outdated. You need to perform the update manually".format(container.name))

