#!/bin/bash
cd /sdcard/omid-ai/
git config --global http.sslVerify false
git add .
git commit -m "Manual Update: ${1:-Save stable state}"
git push origin main
git config --global http.sslVerify true
echo "✅ Your changes are successfully pushed to GitHub!"
