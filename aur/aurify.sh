#!/usr/bin/bash
"micro-script to move things from community to AUR and preserve the history..."

package=$1

git clone --single-branch -b "packages/$package" https://github.com/archlinux/svntogit-community 
cd svntogit-community
git subtree split -b master -P trunk HEAD
git remote set-url origin "aur@aur.archlinux.org:/$package"

# this pleases the hook
git filter-brach --tree-filter 'makepkg --printsrcinfo > .SRCINFO'
git push origin master
