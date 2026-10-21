"""GitHub Release через REST API; секреты остаются только в памяти процесса.

Сначала --check. Публикация требует явного --publish и проверенного ZIP.
GH_TOKEN / GITHUB_TOKEN либо уже настроенный Git Credential Manager.
"""
import argparse
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open("rb") as stream:
        result=hashlib.sha256()
        for block in iter(lambda:stream.read(1024*1024),b""):
            result.update(block)
    return result.hexdigest()


def credential():
    token=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    env={**os.environ,"GIT_TERMINAL_PROMPT":"0","GCM_INTERACTIVE":"Never"}
    result=subprocess.run(["git","-c",f"safe.directory={ROOT.as_posix()}","credential","fill"],
                          input="protocol=https\nhost=github.com\n\n",text=True,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,cwd=ROOT,timeout=30)
    fields=dict(line.split("=",1) for line in result.stdout.splitlines() if "=" in line)
    if result.returncode or not fields.get("password"):
        raise RuntimeError("GitHub authorization unavailable. Sign in with Git Credential Manager or set GH_TOKEN.")
    return fields["password"]


class GitHub:
    def __init__(self,token):
        self.token=token

    def request(self,url,method="GET",payload=None,data=None,content_type=None,missing_ok=False):
        if urlparse(url).hostname not in ("api.github.com","uploads.github.com"):
            raise ValueError("Refusing to send credentials to an unexpected host")
        headers={"Authorization":f"Bearer {self.token}","Accept":"application/vnd.github+json",
                 "X-GitHub-Api-Version":"2022-11-28","User-Agent":"Snake3D-release-tool"}
        if payload is not None:
            data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
            content_type="application/json"
        if content_type:
            headers["Content-Type"]=content_type
        request=Request(url,data=data,headers=headers,method=method)
        try:
            with urlopen(request,timeout=120) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code==404 and missing_ok:
                return None
            try:
                message=json.loads(error.read()).get("message","API request failed")
            except ValueError:
                message="API request failed"
            raise RuntimeError(f"GitHub HTTP {error.code}: {str(message).replace(self.token,'[redacted]')}") from None


def run(args):
    api=GitHub(credential())
    base=f"https://api.github.com/repos/{args.repo}"
    user=api.request("https://api.github.com/user")
    repo=api.request(base)
    release=api.request(f"{base}/releases/tags/{quote(args.tag,safe='')}",missing_ok=True)
    # Черновики также ищем в списке: endpoint по тегу может не показать черновик.
    if release is None:
        release=next((r for r in api.request(f"{base}/releases?per_page=100") if r["tag_name"]==args.tag),None)
    print(json.dumps({"authenticated_as":user["login"],"repository":repo["full_name"],
                      "can_push":repo.get("permissions",{}).get("push"),"release_exists":release is not None}))
    if not args.publish:
        return
    if not args.commit:
        raise RuntimeError("--commit is required for publication")
    game=ROOT/"dist"/"Snake-3D-v1.0-Windows.zip"
    kit=ROOT/"dist"/"Snake-3D-v1.0-itchio-kit.zip"
    verification=game.with_suffix(".verification.json")
    report=json.loads(verification.read_text(encoding="utf-8"))
    if not report["passed"] or report["archive_sha256"]!=digest(game):
        raise RuntimeError("A passing verification report for this exact ZIP is required")
    if report["source_commit"]!=args.commit or report["source_dirty"]:
        raise RuntimeError("Archive must identify the clean commit being released")
    body=(ROOT/"publishing"/"windows"/"RELEASE_NOTES.md").read_text(encoding="utf-8")
    if release is None:
        release=api.request(f"{base}/releases",method="POST",payload={"tag_name":args.tag,"target_commitish":args.commit,
                            "name":"Snake 3D v1.0 — Windows","body":body,"draft":True,"prerelease":False})
    elif release["target_commitish"] not in (args.commit,"main"):
        raise RuntimeError("Existing release points to a different commit; leaving it unchanged")
    files=[game,game.with_suffix(".zip.sha256"),kit]
    assets={asset["name"]:asset for asset in api.request(f"{base}/releases/{release['id']}/assets")}
    checked=[]
    for path in files:
        expected="sha256:"+digest(path)
        asset=assets.get(path.name)
        if asset is None:
            upload=release["upload_url"].split("{",1)[0]+"?"+urlencode({"name":path.name})
            print(f"Uploading {path.name} ({path.stat().st_size:,} bytes)",flush=True)
            asset=api.request(upload,method="POST",data=path.read_bytes(),
                              content_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        asset=api.request(asset["url"])
        if asset["state"]!="uploaded" or asset["size"]!=path.stat().st_size or asset.get("digest")!=expected:
            raise RuntimeError(f"Remote asset verification failed: {path.name}; release not published")
        checked.append({"name":asset["name"],"bytes":asset["size"],"digest":asset["digest"],"url":asset["browser_download_url"]})
    if release["draft"]:
        release=api.request(release["url"],method="PATCH",payload={"draft":False,"body":body,"make_latest":"true"})
    release=api.request(release["url"])
    tag=api.request(f"{base}/git/ref/tags/{quote(args.tag,safe='')}")
    obj=tag["object"]
    if obj["type"]=="tag":
        obj=api.request(obj["url"])["object"]
    if release["draft"] or obj["sha"]!=args.commit:
        raise RuntimeError("Published release/tag verification failed")
    result={"published":True,"release_url":release["html_url"],"tag":args.tag,"commit":args.commit,"assets":checked}
    (ROOT/"artifacts"/"release-publication.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",default="ArishkaWolf/Snake-3D")
    parser.add_argument("--tag",default="v1.0")
    parser.add_argument("--commit")
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--publish",action="store_true")
    arguments=parser.parse_args()
    try:
        run(arguments)
    except Exception as error:
        print(f"Release tool: {error}",file=sys.stderr)
        raise SystemExit(1)
