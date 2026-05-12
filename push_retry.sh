#!/bin/bash
for i in {1..30}; do
  echo "[$(date '+%H:%M:%S')] Attempt $i..."
  GIT_SSH_COMMAND="ssh -i $HOME/.ssh/github_cuzn -o IdentitiesOnly=yes -p 443 -o ConnectTimeout=10" \
    git push ssh://git@ssh.github.com:443/cuzn63449-web/english-learning-app.git master 2>&1 && echo "SUCCESS!" && exit 0
  sleep 600
done
