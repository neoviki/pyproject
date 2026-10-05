#!/bin/bash

if pipx list | grep -q "package pyproject"; then
    read -r -p "A previous installation of pyproject exists and will be removed. Do you wish to continue? [y/n]: " answer

    if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
        echo "Installation cancelled."
        exit 0
    fi

    pipx uninstall pyproject 2>/dev/null 1>/dev/null
fi

pipx install .
