#!/usr/bin/env bash

set -euo pipefail

execute_dir=$(dirname "${0}")
project_dir=$(cd "${execute_dir}" && pwd)

(
  cd "${project_dir}"
  docker-compose --compatibility pull --include-deps --ignore-pull-failures
  docker-compose --compatibility build --force-rm --compress --pull --parallel
  docker-compose --compatibility down --remove-orphans #--volumes
  docker-compose --compatibility up --force-recreate --detach --scale base=0 --scale app=1 --scale worker=1
  cd -
) && echo "Done."
