#!/bin/bash -e
commit_message="$1"
git add .
git commit -a -m "$commit_message"
git push origin master