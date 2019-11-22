#!/usr/bin/python3
import argparse
import os
import shutil


def copy_git_proj_func(*_):
    ignore_items = {'.git', '.idea', '__pycache__', 'docker_installation', 'install_as_container.py'}

    return ignore_items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str, help="Destination docker-container build path")
    args = parser.parse_args()

    dest_path = os.path.join(args.path, 'cq.spam-filter')
    shutil.copytree('docker_installation', dest_path)

    git_proj_app_path = os.path.join(dest_path, 'build', 'app')
    shutil.copytree(os.getcwd(), git_proj_app_path, ignore=copy_git_proj_func)


if __name__ == '__main__':
    main()
