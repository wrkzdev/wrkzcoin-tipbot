#!/bin/bash
pipenv lock -r | cut -d ' ' -f 1 - > requirements.txt
pipenv lock -r --dev | cut -d ' ' -f 1 - > requirements-dev.txt
