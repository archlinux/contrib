#!/usr/bin/python

# SPDX-License-Identifier: GPL-2.0

import io
import os
import tarfile
import tempfile

import requests


def parse_desc(iofile: io.TextIOWrapper):
    store = {}
    blockname = None
    for line in iofile:
        line = line.strip()
        if not line:
            continue
        elif line.startswith("%") and line.endswith("%"):
            blockname = line[1:-1].lower()
            store[blockname] = []
        elif blockname:
            store[blockname].append(line)
    return store


def parse_repo(dbpath):
    pkgfields = ("depends", "makedepends", "optdepends", "checkdepends")
    repodb = tarfile.open(dbpath)
    reponame = os.path.basename(dbpath).split(".")[0]
    pkgs = {}

    for tarinfo in repodb.getmembers():
        if tarinfo.isdir():
            pkgid = tarinfo.name
            desc_tar = repodb.getmember(os.path.join(pkgid, "desc"))
            desc_file = repodb.extractfile(desc_tar)
            desc_file = io.TextIOWrapper(io.BytesIO(desc_file.read()), encoding="UTF-8")
            desc = parse_desc(desc_file)
            del desc_file

            pkgname = desc["name"][0]
            pkgs[pkgname] = {}
            pkgs[pkgname]["repo"] = reponame
            pkgs[pkgname]["arch"] = desc["arch"].pop()

            if "base" in desc:
                pkgs[pkgname]["pkgbase"] = desc["base"][0]

            for key in pkgfields:
                if key in desc:
                    pkgs[pkgname][key] = set(desc[key])

            try:
                depends_tar = repodb.getmember(os.path.join(pkgid, "depends"))
                depends_file = repodb.extractfile(depends_tar)
                depends_file = io.TextIOWrapper(
                    io.BytesIO(depends_file.read()), encoding="UTF-8"
                )
                depends = parse_desc(depends_file)
                del depends_file

                for key in pkgfields:
                    if key in depends:
                        try:
                            pkgs[pkgname][key].update(depends[key])
                        except KeyError:
                            pkgs[pkgname][key] = set(depends[key])
            except KeyError:
                pass

            # remove descriptions from optional dependencies
            if "optdepends" in pkgs[pkgname]:
                pkgs[pkgname]["optdepends"] = {
                    optdep.split(":")[0] for optdep in pkgs[pkgname]["optdepends"]
                }

            # remove version requirements
            for key in pkgfields:
                if key in pkgs[pkgname]:
                    tmp = pkgs[pkgname][key]
                    for ch in ("<", ">", "="):
                        tmp = {dep.split(ch)[0] if ch in dep else dep for dep in tmp}

                    pkgs[pkgname][key] = tmp

            # assign empty sets to missing fields
            for key in pkgfields:
                if key not in pkgs[pkgname]:
                    pkgs[pkgname][key] = set()

    return pkgs


def get_orphans():
    base_url = "https://www.archlinux.org/packages/search/json/?maintainer=orphan"
    query = "repo=Community&repo=Core&repo=Extra&repo=Multilib"
    response = requests.get(f"{base_url}&{query}").json()
    num_pages = response["num_pages"]

    results = response["results"]

    if num_pages > 1:
        for page in range(2, num_pages + 1):
            response = requests.get(f"{base_url}&{query}&page={page}").json()
            results.extend(response["results"])

    return {pkg["pkgname"] for pkg in results}


def get_packages(mirror="http://mirror.pkgbuild.com"):
    pkgs = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        for repo in ("core", "extra", "community", "multilib"):
            url = f"{mirror}/{repo}/os/x86_64/{repo}.db"
            response = requests.get(url)

            dbpath = f"{tmpdir}/{repo}.db"
            with open(dbpath, "wb") as f:
                f.write(response.content)

            pkgs.update(parse_repo(dbpath))

    return pkgs


def find_unneeded_orphans(pkgs, orphans):
    required = {
        dep
        for pkg in pkgs
        for key in ("depends", "makedepends", "optdepends", "checkdepends")
        for dep in pkgs[pkg][key]
    }

    return orphans - required


def what_requires(pkgs, pkgname):
    deptypes = ("depends", "makedepends", "checkdepends")
    required_by = set()

    for pkg in pkgs:
        for deptype in deptypes:
            if pkgname in pkgs[pkg][deptype]:
                required_by.add(pkg)

    return required_by


def get_maintainers(repo, arch, pkgname):
    url = f"https://www.archlinux.org/packages/{repo}/{arch}/{pkgname}/json/"
    response = requests.get(url)
    return response.json()["maintainers"]


def main():
    packages = get_packages()
    archweb_orphans = get_orphans()

    unneeded = find_unneeded_orphans(packages, archweb_orphans)
    required_orphans = {}

    for orphan in archweb_orphans - unneeded:
        packages[orphan]["required_by"] = what_requires(packages, orphan)

        if packages[orphan]["required_by"].issubset(archweb_orphans):
            unneeded.add(orphan)
        else:
            required_orphans[orphan] = {}
            required_orphans[orphan]["by-pkg"] = {}
            for pkg in packages[orphan]["required_by"]:
                if "maintainers" not in packages[pkg]:
                    maintainers = get_maintainers(
                        packages[pkg]["repo"], packages[pkg]["arch"], pkg
                    )
                    packages[pkg]["maintainers"] = maintainers
                    required_orphans[orphan]["by-pkg"][pkg] = maintainers
                else:
                    required_orphans[orphan]["by-pkg"][pkg] = packages[pkg][
                        "maintainers"
                    ]

    print("Orphans required by maintained packages:")
    for orphan in sorted(required_orphans.keys()):
        required_orphans[orphan]["by-maint"] = {}
        for pkg in required_orphans[orphan]["by-pkg"]:
            for maint in required_orphans[orphan]["by-pkg"][pkg]:
                if maint not in required_orphans[orphan]["by-maint"]:
                    required_orphans[orphan]["by-maint"][maint] = set()

                required_orphans[orphan]["by-maint"][maint].add(pkg)

        print(f"- {orphan}:")
        for maint in required_orphans[orphan]["by-maint"]:
            maint_pkgs = ", ".join(
                list(required_orphans[orphan]["by-maint"][maint])[:3]
            )
            print(f"    {maint}: {maint_pkgs}")

    print("")
    print("Unneeded orphans:")
    print("\n".join(sorted(unneeded)))


if __name__ == "__main__":
    main()
