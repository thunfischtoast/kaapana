from time import time
import json
import networkx as nx
# import matplotlib.pyplot as plt
from os.path import join, dirname, basename, exists, isfile, isdir


class BuildUtils:
    container_images_available = None
    container_images_unused = None
    charts_available = None
    charts_unused = None
    base_images_used = None
    logger = None
    kaapana_dir = None
    default_registry = None
    platform_filter = None
    external_source_dirs = None
    issues_list = None
    exit_on_error = True
    build_graph = None
    
    @staticmethod
    def add_container_images_available(container_images_available):
        BuildUtils.container_images_available = container_images_available
        BuildUtils.container_images_unused = container_images_available.copy()

    @staticmethod
    def add_charts_available(charts_available):
        BuildUtils.charts_available = charts_available
        BuildUtils.charts_unused = charts_available.copy()

    @staticmethod
    def init(kaapana_dir, build_dir, external_source_dirs, platform_filter, default_registry, http_proxy, logger,exit_on_error):
        BuildUtils.logger = logger
        BuildUtils.kaapana_dir = kaapana_dir
        BuildUtils.build_dir = build_dir
        BuildUtils.platform_filter = platform_filter
        BuildUtils.default_registry = default_registry
        BuildUtils.http_proxy = http_proxy
        BuildUtils.external_source_dirs = external_source_dirs
        BuildUtils.exit_on_error = exit_on_error
        BuildUtils.issues_list = []
        BuildUtils.build_graph = nx.DiGraph(directed=True)
        BuildUtils.build_graph.add_node("ROOT")
        BuildUtils.base_images_used = []

    @staticmethod
    def get_timestamp():
        return str(int(time() * 1000))
    
    @staticmethod
    def get_build_order():
        build_order_bottom_up = list(reversed(list(nx.topological_sort(BuildUtils.build_graph))))
        return build_order_bottom_up

    @staticmethod
    def make_log(output):
        std_out = output.stdout.split("\n")[-100:]
        log = {}
        len_std = len(std_out)
        for i in range(0, len_std):
            log[i] = std_out[i]
        std_err = output.stderr.split("\n")
        for err in std_err:
            if err != "":
                len_std += 1
                log[len_std] = f"ERROR: {err}"
        return log

    @staticmethod
    def generate_issue(component, name, level, msg, path="", output=None):
        log = ""
        if output != None:
            log = BuildUtils.make_log(output)
            BuildUtils.logger.error("LOG:")
            BuildUtils.logger.error(log)

        issue = {
            "component": component,
            "name": name,
            "level": level,
            "log": log,
            "msg": msg,
            "timestamp": BuildUtils.get_timestamp(),
            "filepath": path,
        }
        BuildUtils.issues_list.append(issue)
        
        if level == "FATAL":
            exit(1)
        elif level == "WARN":
            BuildUtils.logger.warn(f"Added issue:")
            BuildUtils.logger.warn(json.dumps(issue, indent=4, sort_keys=True))
        elif BuildUtils.exit_on_error:
            exit(1)
        else:
            BuildUtils.logger.debug("Added issue:")
            BuildUtils.logger.debug(json.dumps(issue, indent=4, sort_keys=True))

    @staticmethod
    def generate_containers_info():
        unused_containers_json_path = join(BuildUtils.build_dir, "unused_containers.json")
        BuildUtils.logger.debug("")
        BuildUtils.logger.debug("Collect unused containers:")
        BuildUtils.logger.debug("")
        unused_container=[]
        for container in BuildUtils.container_images_unused:
            BuildUtils.logger.info(f"{container.tag}")
            unused_container.append(container.get_dict())
        with open(unused_containers_json_path, 'w') as fp:
            json.dump(unused_container, fp, indent=4)

        base_images_json_path = join(BuildUtils.build_dir, "base_images.json")
        base_images=[]
        BuildUtils.logger.debug("")
        BuildUtils.logger.debug("Collect base-images:")
        BuildUtils.logger.debug("")
        for base_image in BuildUtils.base_images_used:
            BuildUtils.logger.info(f"{base_image.tag}")
            base_images.append(base_image.get_dict())
        with open(base_images_json_path, 'w') as fp:
            json.dump(base_images, fp, indent=4)

        all_containers_json_path = join(BuildUtils.build_dir, "containers_all.json")
        BuildUtils.logger.debug("")
        BuildUtils.logger.debug("Collect all containers present:")
        BuildUtils.logger.debug("")
        all_container=[]
        for container in BuildUtils.container_images_available:
            BuildUtils.logger.info(f"{container.tag}")
            all_container.append(container.get_dict())

        all_containers_json_path = join(BuildUtils.build_dir, "containers_all.json")
        with open(all_containers_json_path, 'w') as fp:
            json.dump(all_container, fp, indent=4)

if __name__ == '__main__':
    print("Please use the 'start_build.py' script to launch the build-process.")
    exit(1)