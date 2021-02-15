#!/bin/bash
# Copyright (c) 2021 Konstantin Gizdov
# SPDX-License-Identifier: GPL-2.0

# current working directory
__CWKDIR="${PWD}"
# script directory
__SCRDIR="$(cd "$(dirname "$0")" && pwd)"

__EXEC_NAME="parse-submodules"
__PRSSUB_VERSION_MAJOR__="0"
__PRSSUB_VERSION_MINOR__="0"
__PRSSUB_VERSION_PATCH__="1"
__PRSSUB_VERSION__="${__PRSSUB_VERSION_MAJOR__}.${__PRSSUB_VERSION_MINOR__}.${__PRSSUB_VERSION_PATCH__}"
__SHALLOW_CLONE=1
__VERBOSE_MODE=0
__VERBOSE_PIPE='2'
__SILENT_PIPE='/dev/null'
__PIPE="${__SILENT_PIPE}"
__DRY_RUN=0

function err_echo {
    # echo to default error descriptor
    >&2 echo "${*}"
}

function verbose_echo {
    # only print to screen when second argument is 1
    [[ ${2} == 1 ]] && err_echo "${1}"
    return 0
}

function fail {
    # fail with error message
    err_echo "${1}"
    exit "${2:-1}"  # return a code specified by $2 or $1
}

function version {
    echo "${__EXEC_NAME} version ${__PRSSUB_VERSION__}"
}

function help {
    # print info & help
    version
    echo ""
    echo "Usage: $0 [options] <GIT REPO REMOTE URL> [<GIT REF>]

    A utility to parse and print out useful information about
    a Git repository's submodule paths and URLs.

arguments:
    GIT REPO REMOTE URL: the URL of the remote Git repository (required)
    GIT REF: Git repository reference to use (optional, default: HEAD)

options:
    -n  dry run: skip all actions that incur any changes

helper options:
    -v  verbose mode

    -V  print version and exit

    -h  print this help message and exit
"
}

function check-submodules {
    local _ref="${1:-${__GIT_REF}}"
    verbose_echo "Checking if submodules exist for Git reference: ${_ref}" ${__VERBOSE_MODE}
    git ls-tree --full-name --name-only -r "${_ref}" | grep .gitmodules &>${__PIPE}
}

function check-existance {
    local _repo_url="${1}"
    verbose_echo "Checking access to Git repository at: ${_repo_url}" ${__VERBOSE_MODE}
    git ls-remote "${_repo_url}" CHECK_GIT_REMOTE_URL_REACHABILITY &>${__PIPE}
}

function check-git-archive {
    local _repo_url="${1}"
    verbose_echo "Checking archive support of Git repository: ${_repo_url}" ${__VERBOSE_MODE}
    git archive --remote="${_repo_url}" --list &>${__PIPE}
}

function check-branch-or-tag {
    local _repo_url="${1}"
    local _ref="${2}"
    verbose_echo "Checking if given Git reference '${_ref}' is a branch or tag name of repository at: ${_repo_url}" ${__VERBOSE_MODE}
    local _branch="$(git ls-remote --symref "${_repo_url}" "${_ref}" | grep -v 'ref:' | awk '{sub(/refs\/(heads|tags)\//, "", $2); print $2}' | head -n1)"
    if [[ -z $_branch ]]; then
        verbose_echo "Reference in not a tag, branch or other symbolic reference that can be used for remote clone reference." ${__VERBOSE_MODE}
        return 1
    elif [[ "$_branch" == "HEAD" ]]; then
        verbose_echo "Reference 'HEAD' of Git repository at '${_repo_url}' points to the default branch and can be converted to a symbolic link for shallow clone." ${__VERBOSE_MODE}
    else
        verbose_echo "Reference branch or tag of Git repository at '${_repo_url}' is '"${_branch}"'" ${__VERBOSE_MODE}
    fi
    return 0
}

function get-file-from-archive {
    local _repo_url="${1}"
    local _ref="${2}"
    local _module_file="${3}"
    verbose_echo "Getting archive of ${_module_file} from ${_repo_url} with reference ${_ref}" ${__VERBOSE_MODE}
    local gmf="$(git archive --remote="${_repo_url}" "${_ref}" "${_module_file}" 2>/dev/null)"
    echo "${gmf}" | tar -x
    local _ret=$?
    [[ $_ret -eq 0 ]] || fail "Could not find the Git submodule config file '.gitmodules'." $_ret
}

function get-submodules-file {
    local _ref="${1:-${__GIT_REF}}"
    verbose_echo "Checking if submodule config file exists for Git reference: ${_ref}" ${__VERBOSE_MODE}
    git ls-tree --full-name --name-only -r "${_ref}" | grep '.gitmodules' | head -n1
}


function get-short-hash {
    local _repo_url="${1}"
    local _ref="${2}"
    verbose_echo "Getting short hash of Git reference '${_ref}' from repository at: ${_repo_url}" ${__VERBOSE_MODE}
    local _short_ref="$(git ls-remote "${_repo_url}" "${_ref}" | awk '{ print substr($1,1,10) }' | head -n1)"
    if [[ -z $_short_ref ]]; then
        _short_ref="$(echo "${_ref}" | awk '{ print substr($1,1,10) }')"
        verbose_echo "Reference in not symbolic. Shortening '${_ref}' to '${_short_ref}'" ${__VERBOSE_MODE}
    fi
    verbose_echo "Short hash of Git reference '${_ref}' from repository '${_repo_url}' is: ${_short_ref}" ${__VERBOSE_MODE}
    echo "${_short_ref}"
}

function get-branch-or-tag {
    local _repo_url="${1}"
    local _ref="${2}"
    local _branch=""
    if ! check-branch-or-tag "${_repo_url}" "${_ref}"; then
        verbose_echo "Cannot get branch or tag name for Git reference '${_ref}' from repository at '${_repo_url}'." ${__VERBOSE_MODE}
        echo ''
        return 1
    elif [[ "${_ref}" == "HEAD" ]]; then
        _branch="$(git ls-remote --symref "${_repo_url}" HEAD | grep 'ref:' | awk '{sub(/refs\/(heads|tags)\//, "", $2); print $2}' | head -n1)"
        verbose_echo "Converting 'HEAD' to default branch of Git repository at '${_repo_url}': '"${_branch}"'" ${__VERBOSE_MODE}
    else
        verbose_echo "Getting branch or tag name of Git reference '${_ref}' from repository at: ${_repo_url}" ${__VERBOSE_MODE}
        _branch="$(git ls-remote --symref "${_repo_url}" "${_ref}" | grep -v 'ref:' | awk '{sub(/refs\/(heads|tags)\//, "", $2); print $2}' | head -n1)"
    fi
    verbose_echo "Reference branch or tag of Git repository at '${_repo_url}' is '"${_branch}"'" ${__VERBOSE_MODE}
    echo "${_branch}"
}

function get-reference-hash {
    local _repo_url="${1}"
    local _ref="${2}"
    verbose_echo "Getting hash of Git reference '${_ref}' from repository at: ${_repo_url}" ${__VERBOSE_MODE}
    local _hash="$(git ls-remote "${_repo_url}" "${_ref}" | awk '{print $1}' | head -n1)"
    verbose_echo "Hash of Git reference '${_ref}' from repository '${_repo_url}' is '"${_hash}"'" ${__VERBOSE_MODE}
    echo "${_hash}"
}

function get-module-names {
    git config --file "${1}" --get-regexp path | awk -F'.' '{print $2}'
}

function get-module-urls {
    git config --file "${1}" --get-regexp url | awk '{print $2}'
}

function get-module-url {
    git config --file "${1}" --get-regexp url | grep "${2}.url" | awk '{print $2}'
}

function get-module-paths {
    git config --file "${1}" --get-regexp path | awk '{print $2}'
}

function get-module-path {
    git config --file "${1}" --get-regexp path | grep "${2}.path" | awk '{print $2}'
}

function get-proto {
    # Extract the protocol (includes trailing "://").
    local __PROTO="$(echo "${1}" | sed -nr 's,^(.*://).*,\1,p')"
    verbose_echo "URL protocol: ${__PROTO}" ${__VERBOSE_MODE}
    echo "${__PROTO}"
}

function get-url-noproto {
    # Remove the protocol from the URL.
    local __URL="$(echo ${1/$(get-proto "${1}")/})"
    verbose_echo "URL without protocol: ${__URL}" ${__VERBOSE_MODE}
    echo "${__URL}"
}

function get-url-noproto-nouser {
    # Remove the protocol from the URL.
    local __noproto="$(get-url-noproto "${1}")"
    local __URL="$(echo ${__noproto/$(get-user "${1}")/})"
    verbose_echo "URL without protocol and without user: ${__URL}" ${__VERBOSE_MODE}
    echo "${__URL}"
}

function get-url-noproto-nouser-noport {
    # Remove the protocol from the URL.
    local __noproto_nouser="$(get-url-noproto-nouser "${1}")"
    local __URL="$(echo ${__noproto_nouser/$(get-port "${1}")/})"
    verbose_echo "URL without protocol, user or port: ${__URL}" ${__VERBOSE_MODE}
    echo "${__URL}"
}

function get-user {
    # Extract the user (includes trailing "@").
    local __USER="$(echo "$(get-url-noproto "${1}")" | sed -nr 's,^(.*@).*,\1,p')"
    verbose_echo "USER: ${__USER}" ${__VERBOSE_MODE}
    echo "${__USER}"
}

function get-port {
    local __noproto_nouser="$(get-url-noproto-nouser "${1}")"
    local __PORT="$(echo "${__noproto_nouser}" | sed -nr 's,.*(:[0-9]+).*,\1,p')"
    verbose_echo "PORT: ${__USER}" ${__VERBOSE_MODE}
    echo "${__PORT}"
}

function get-path {
    local __PATH="$(echo "$(get-url-noproto-nouser-noport "${1}")" | sed -nr 's,[^/:]*([/:].*),\1,p')"
    verbose_echo "PATH: ${__USER}" ${__VERBOSE_MODE}
    echo "${__PATH}"
}

function get-host {
    local __noproto_nouser_noport="$(get-url-noproto-nouser-noport "${1}")"
    local __HOST="$(echo ${__noproto_nouser_noport/$(get-path "${1}")/})"
    verbose_echo "HOST: ${__USER}" ${__VERBOSE_MODE}
    echo "${__HOST}"
}

function get-repo-name {
    local _repo_url="${1}"
    local _repo_name="$(basename --suffix='.git' "${_repo_url}")"
    verbose_echo "Git repository at ${_repo_url} is named: ${_repo_name}" ${__VERBOSE_MODE}
    echo "${_repo_name}"
}

function get-repo-suffix-path {
    local __url_path="$(get-path "${1}")"
    local __PATH="$(realpath -m //"${__url_path}"/"${2}")"
    if [[ "${__url_path:0:1}" == ':' ]]; then
        __PATH=":${__PATH:1}"
    fi
    echo "${__PATH}"
}

function shallow_clone {
    local _repo_url="${1}"
    local _ref="${2}"
    local _destdir="${3:-"./$(get-repo-name "${_repo_url}")"}"
    local _symref="$(get-branch-or-tag "${_repo_url}" "${_ref}")"
    verbose_echo "Shallow-cloning ${_repo_url} at reference ${_symref} into ${_destdir}." ${__VERBOSE_MODE}
    git clone --no-checkout --depth 1 -b "${_symref}" "${_repo_url}" "${_destdir}" &>${__PIPE} || fail "Repository shallow clone failed." 1
}

function full_clone {
    local _repo_url="${1}"
    local _ref="${2}"
    local _destdir="${3:-"./$(get-repo-name "${_repo_url}")"}"
    local _pwd="$(pwd)"
    verbose_echo "Cloning ${_repo_url} at reference ${_ref} into ${_destdir}." ${__VERBOSE_MODE}
    git clone "${_repo_url}" "${_destdir}" &>${__PIPE} || fail "Repository clone failed." 1
    cd "${_destdir}"
    git reset --hard "${_ref}" &>${__PIPE} || fail "Reference ${_ref} checkout failed." 1
    cd "${_pwd}"
}

function print_submodule_url {
    local _mod_url="${1}"
    local _remote_prefix="${2}"
    local _repo_url="${3}"
    local _outfile="${4}"
    if ! check-existance "${_mod_url}"; then
        echo "  ${_remote_prefix}$(get-repo-suffix-path "${_repo_url}" "${_mod_url}")" >>"${_outfile}"
    else
        echo "  ${_mod_url}" >>"${_outfile}"
    fi
}

if ! command -v git &> /dev/null; then
    fail "'git' command not found." 1
fi

if [[ $# < 1 ]]; then
    fail "$(help)" 1
fi

tempdir="$(mktemp -d)"
gcldir="${tempdir}/gitdir"
gmdfile="${tempdir}/found_gitmodules"
outfile="${tempdir}/out"
trap "rm -rf ${tempdir}; cd ${__CWKDIR}" EXIT

cd "${tempdir}"

while getopts "Vvnh" opt; do
    case $opt in
        v)
            __VERBOSE_MODE=1
            __PIPE="${__VERBOSE_PIPE}"
            ;;
        n)
            __DRY_RUN=1
            ;;
        V)
            version
            exit 0
            ;;
        h)
            help
            exit 0
            ;;
        :)
            help
            fail "Option -${OPTARG} needs an argument." 1
            ;;
        \?)
            help
            fail "Invalid option -- '${OPTARG:-${!OPTIND:-${opt:-}}}'" 1
            ;;
    esac
done

__GIT_REMOTE=${@:$OPTIND:1}
__GIT_REF=${@:$OPTIND+1:1}
if [ -z $__GIT_REMOTE ]; then
    fail "$(help)" 1
fi

# this needs to happen before checking for default branch
if ! check-existance "${__GIT_REMOTE}"; then
    fail "Git repository ${__GIT_REMOTE} not found or not accessible." 1
fi

if [ -z $__GIT_REF ]; then
    __GIT_REF='HEAD'
fi

verbose_echo "Checking repository ${__GIT_REMOTE} with ref ${__GIT_REF}..." ${__VERBOSE_MODE}

# can we use git archive
__USE_ARCHIVE=1
if ! check-git-archive "${__GIT_REMOTE}"; then
    verbose_echo "Git remote of ${__GIT_REMOTE} does not support git-archive. Cloning entire repository..." ${__VERBOSE_MODE}
    __USE_ARCHIVE=0
fi

if [[ ${__USE_ARCHIVE} == 1 ]]; then
    # get .gitmodules with git archive
    get-file-from-archive "${__GIT_REMOTE}" "${__GIT_REF}" '.gitmodules'
    cp '.gitmodules' "${gmdfile}"
else
    # shallow clone repository locally
    if ! check-branch-or-tag "${__GIT_REMOTE}" "${__GIT_REF}" ; then
        # shallow clone is not possible
        err_echo "Warning: Shallow clone is not possible for exact commit hashes. Preferably use a tag for better performance."
        full_clone "${__GIT_REMOTE}" "${__GIT_REF}" "${gcldir}"
    else
        shallow_clone "${__GIT_REMOTE}" "${__GIT_REF}" "${gcldir}"
    fi
    cd "${gcldir}"
    if ! check-submodules "${__GIT_REF}"; then
        fail "'.gitmodules' file does not exist in repo." 1
    fi
    __SUBMOD_FILE="$(get-submodules-file "${__GIT_REF}")"
    git --no-pager --git-dir "${gcldir}/.git" show "${__GIT_REF}":"${__SUBMOD_FILE}" >"${gmdfile}"
fi
cd "${tempdir}"
touch "${outfile}"
__SHORT_HASH="$(get-short-hash "${__GIT_REMOTE}" "${__GIT_REF}")"
echo '# Your sources array should look something like:
sources=(
  "${pkgname}::'${__GIT_REMOTE}'#commit='${__SHORT_HASH}'"' >>"${outfile}"
__REMOTE_PREFIX="$(get-proto "${__GIT_REMOTE}")$(get-user "${__GIT_REMOTE}")$(get-host "${__GIT_REMOTE}")$(get-port "${__GIT_REMOTE}")"
for name in $(get-module-names "${gmdfile}"); do
    __mod_url="$(get-module-url "${gmdfile}" "${name}")"
    # this is slow so run in parallel, store PIDs and wait on all later
    print_submodule_url "${__mod_url}" "${__REMOTE_PREFIX}" "${__GIT_REMOTE}" "${outfile}" &
    pids="$pids $!"
done
for pid in $pids; do
    # wait for all PIDs from above
    wait $pid
done
echo ')' >>"${outfile}"

echo '# Put the following in your PKGBUILD prepare function:
prepare() {
  cd "${srcdir}/${pkgname}"
  git submodule init
' >>"${outfile}"
for name in $(get-module-names "${gmdfile}"); do
    echo '  git config submodule."'${name}'".url "${srcdir}"/'"$(get-repo-name "$(get-module-url "${gmdfile}" "${name}")")" >>"${outfile}"
done
echo '  git submodule update --recursive
}' >>"${outfile}"

cat "${outfile}"
