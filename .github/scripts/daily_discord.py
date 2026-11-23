#!/usr/bin/env python3
"""Send a KST calendar-day repository activity summary using Python's stdlib."""

import argparse
from datetime import date, datetime, time as dt_time, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
UTC = timezone.utc
ACTIVITY_TYPES = {"push", "force_push", "pr_merge", "merge_queue_merge", "branch_creation"}
GITHUB_LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")


class ReportError(RuntimeError):
    """A safe-to-display error that never contains credentials or webhook URLs."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def report_window(report_date=None, now=None):
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ReportError("현재 시각에는 시간대 정보가 필요합니다.")
    today = now.astimezone(KST).date()
    if report_date:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", report_date):
            raise ReportError("집계 날짜는 YYYY-MM-DD 형식이어야 합니다.")
        try:
            day = date.fromisoformat(report_date)
        except ValueError:
            raise ReportError("유효하지 않은 집계 날짜입니다.") from None
    else:
        day = today - timedelta(days=1)
    if not today - timedelta(days=30) <= day < today:
        raise ReportError("집계 날짜는 한국 시간 기준 어제부터 30일 전까지 선택할 수 있습니다.")
    start = datetime.combine(day, dt_time.min, KST)
    end = datetime.combine(day + timedelta(days=1), dt_time.min, KST)
    return day, start.astimezone(UTC), end.astimezone(UTC)


def load_config(path):
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ReportError("멤버 설정 파일을 UTF-8 JSON 형식으로 확인하세요.") from None
    if not isinstance(config, dict):
        raise ReportError("멤버 설정은 JSON 객체여야 합니다.")
    branch = config.get("branch", "main")
    if not isinstance(branch, str) or len(branch) > 240:
        raise ReportError("branch는 브랜치 이름 또는 빈 문자열이어야 합니다.")
    branch = branch.strip().removeprefix("refs/heads/")
    if branch.startswith("refs/") or "\n" in branch or "\r" in branch:
        raise ReportError("branch에는 태그가 아닌 브랜치 이름을 입력하세요.")
    kinds = config.get("activity_types", ["push", "force_push"])
    if not isinstance(kinds, list) or not kinds or any(
        not isinstance(kind, str) or kind not in ACTIVITY_TYPES for kind in kinds
    ):
        raise ReportError("activity_types에 지원하는 활동 종류를 입력하세요.")
    members = config.get("members")
    if not isinstance(members, list) or not 1 <= len(members) <= 30:
        raise ReportError("members에는 실제 스터디원 1~30명의 GitHub ID를 입력하세요.")
    seen, normalized = set(), []
    for member in members:
        if not isinstance(member, dict):
            raise ReportError("각 멤버는 github와 name을 가진 객체여야 합니다.")
        login, name = member.get("github"), member.get("name")
        if not isinstance(login, str) or not GITHUB_LOGIN.fullmatch(login) or "--" in login:
            raise ReportError("멤버 github에는 @ 없이 실제 GitHub 사용자 ID를 입력하세요.")
        if login.casefold() in seen:
            raise ReportError("멤버 목록에 중복된 GitHub ID가 있습니다.")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 40 or any(
            ord(char) < 32 for char in name
        ):
            raise ReportError("멤버 name은 줄바꿈 없는 1~40자 이름이어야 합니다.")
        seen.add(login.casefold())
        normalized.append({"github": login, "name": name.strip()})
    return {"branch": branch, "activity_types": kinds, "members": normalized}


def parse_timestamp(value):
    if not isinstance(value, str):
        raise ReportError("GitHub 활동 기록에 시각이 없습니다. 발송을 중단합니다.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ReportError("GitHub 활동 시각을 해석하지 못했습니다.") from None
    if parsed.tzinfo is None:
        raise ReportError("GitHub 활동 시각에 시간대가 없습니다.")
    return parsed.astimezone(UTC)


def normalize_activity(item):
    if not isinstance(item, dict) or not isinstance(item.get("id"), (str, int)):
        raise ReportError("GitHub 활동 응답 형식이 예상과 다릅니다.")
    kind = item.get("activity_type")
    actor, stamp = item.get("actor"), item.get("timestamp")
    if kind is None and "push_type" in item:
        kind = {"normal": "push", "force": "force_push"}.get(item["push_type"])
        actor, stamp = item.get("pusher"), item.get("pushed_at")
    if not isinstance(kind, str) or not isinstance(item.get("ref"), str):
        raise ReportError("GitHub 활동 종류 또는 브랜치 정보가 없습니다.")
    if actor is not None and (
        not isinstance(actor, dict) or not isinstance(actor.get("login"), str)
        or not actor["login"]
    ):
        raise ReportError("GitHub 활동 사용자를 확인하지 못했습니다.")
    return {"id": str(item["id"]), "timestamp": parse_timestamp(stamp),
            "activity_type": kind, "actor": actor, "ref": item["ref"]}


def github_get(url, token):
    request = Request(url, headers={
        "Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "WinterNagi-Daily-Report",
    })
    opener = build_opener(NoRedirect())
    for attempt in range(3):
        try:
            with opener.open(request, timeout=30) as response:
                return json.load(response), dict(response.headers)
        except HTTPError as error:
            if attempt < 2 and (error.code == 429 or 500 <= error.code < 600):
                time.sleep(1 + attempt)
                continue
            raise ReportError(f"GitHub 조회 실패(HTTP {error.code}). 발송하지 않았습니다.") from None
        except (URLError, TimeoutError, ConnectionError):
            if attempt < 2:
                time.sleep(1 + attempt)
                continue
            raise ReportError("GitHub 연결 실패. 발송하지 않았습니다.") from None
        except (json.JSONDecodeError, UnicodeError):
            raise ReportError("GitHub에서 정상 JSON을 받지 못했습니다. 발송하지 않았습니다.") from None


def next_cursor(headers):
    link = next((v for k, v in headers.items() if k.lower() == "link"), "")
    for part in link.split(","):
        if not re.search(r';\s*rel="next"', part):
            continue
        match = re.match(r"\s*<([^>]+)>", part)
        if not match:
            raise ReportError("GitHub 페이지 이동 정보를 해석하지 못했습니다.")
        parsed = urlsplit(match[1])
        if parsed.scheme != "https" or parsed.netloc != "api.github.com":
            raise ReportError("GitHub 페이지 이동 주소가 예상과 다릅니다.")
        cursor = parse_qs(parsed.query).get("after", [])
        if len(cursor) != 1 or not cursor[0]:
            raise ReportError("GitHub 다음 페이지 커서가 없습니다.")
        # Rebuild the original URL, never send credentials to a URL from the response.
        return cursor[0]
    return None


def fetch_activities(repository, token, start, end, branch="", get_page=None):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository or ""):
        raise ReportError("GITHUB_REPOSITORY에 owner/repository가 필요합니다.")
    if not token:
        raise ReportError("GitHub 조회용 GITHUB_TOKEN이 없습니다.")
    get_page = get_page or github_get
    base = f"https://api.github.com/repos/{repository}/activity"
    params = {"direction": "desc", "per_page": 100}
    if branch:
        params["ref"] = f"refs/heads/{branch}"
    records, seen_ids, seen_cursors = [], set(), set()
    previous = None
    for _ in range(100):
        page, headers = get_page(base + "?" + urlencode(params), token)
        if not isinstance(page, list) or len(page) > 100:
            raise ReportError("GitHub 활동 목록이 불완전합니다. 발송을 중단합니다.")
        older = False
        for item in page:
            activity = normalize_activity(item)
            stamp = activity["timestamp"]
            if previous is not None and stamp > previous:
                raise ReportError("GitHub 활동 정렬을 확인하지 못했습니다. 발송을 중단합니다.")
            previous = stamp
            if stamp < start:
                older = True
            if start <= stamp < end and activity["id"] not in seen_ids:
                records.append(activity)
            seen_ids.add(activity["id"])
        if older:
            return records
        cursor = next_cursor(headers)
        if cursor is None:
            return records
        if not page or cursor in seen_cursors:
            raise ReportError("GitHub 페이지 조회가 반복되거나 누락됐습니다. 발송을 중단합니다.")
        seen_cursors.add(cursor)
        params["after"] = cursor
    raise ReportError("GitHub 조회가 100페이지를 초과했습니다. 불완전한 집계는 발송하지 않습니다.")


def escape_markdown(value):
    return re.sub(r"([\\`*_{}\[\]()<>#+\-.!|~])", r"\\\1", value).replace("@", "＠")


def render_message(config, activities, day, repository):
    pushed = set()
    for activity in activities:
        if activity["activity_type"] not in config["activity_types"]:
            continue
        ref = activity["ref"]
        if not ref.startswith("refs/heads/") or (
            config["branch"] and ref != f"refs/heads/{config['branch']}"
        ):
            continue
        if activity["actor"] is None:
            raise ReportError("작성자를 확인할 수 없는 활동이 있어 멤버 분류를 발송하지 않습니다.")
        pushed.add(activity["actor"]["login"].casefold())
    present, absent = [], []
    for member in config["members"]:
        label = f"• {escape_markdown(member['name'])} ({escape_markdown(member['github'])})"
        (present if member["github"].casefold() in pushed else absent).append(label)
    scope = escape_markdown(config["branch"]) if config["branch"] else "전체 브랜치"
    kinds = ", ".join(config["activity_types"])
    content = "\n".join([
        f"📘 **{escape_markdown(repository.split('/')[-1])} · {day.isoformat()} 업로드 기록**",
        f"한국 시간 00:00–24:00 · {scope}", "",
        "**✅ Push 기록 있는 멤버**", *(present or ["• 없음"]), "",
        "**🌙 Push 기록 없는 멤버**", *(absent or ["• 없음"]), "",
    ])
    if len(content.encode("utf-16-le")) // 2 > 2000:
        raise ReportError("메시지가 Discord의 2,000자 한도를 초과합니다. 이름을 줄여 주세요.")
    return content


def discord_url(raw):
    try:
        parsed = urlsplit(raw.strip())
    except (ValueError, AttributeError):
        raise ReportError("DISCORD_WEBHOOK_URL에 유효한 Discord 웹훅 주소가 필요합니다.") from None
    if parsed.path.rstrip("/").endswith("/github"):
        raise ReportError("DISCORD_WEBHOOK_URL에는 /github를 제거한 원래 웹훅 주소를 넣으세요.")
    if (parsed.scheme != "https" or parsed.netloc not in {"discord.com", "discordapp.com"}
            or parsed.fragment or not re.fullmatch(
                r"/api(?:/v\d+)?/webhooks/\d+/[A-Za-z0-9_-]+/?", parsed.path)):
        raise ReportError("DISCORD_WEBHOOK_URL에 유효한 Discord 웹훅 주소가 필요합니다.")
    if parsed.query and set(parse_qs(parsed.query, keep_blank_values=True)) - {"wait"}:
        raise ReportError("일반 텍스트 채널의 원래 웹훅 URL을 사용하세요. 스레드 옵션은 지원하지 않습니다.")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "wait=true", ""))


def post_discord(raw_url, content):
    url = discord_url(raw_url)
    body = json.dumps({"content": content, "allowed_mentions": {"parse": []}}, ensure_ascii=False).encode()
    request = Request(url, data=body, headers={"Content-Type": "application/json",
                      "User-Agent": "WinterNagi-Daily-Report"}, method="POST")
    opener = build_opener(NoRedirect())
    for attempt in range(3):
        try:
            with opener.open(request, timeout=30) as response:
                result = json.load(response)
            if not isinstance(result, dict) or not isinstance(result.get("id"), str):
                raise ReportError("Discord 발송 확인을 받지 못했습니다. 채널을 확인한 뒤 재실행하세요.")
            return result["id"]
        except HTTPError as error:
            if error.code == 429 and attempt < 2:
                try:
                    delay = float(json.load(error).get("retry_after"))
                except (ValueError, TypeError, json.JSONDecodeError, AttributeError):
                    delay = 11
                if 0 <= delay <= 10:
                    time.sleep(delay + 0.1)
                    continue
            raise ReportError(f"Discord 발송 실패(HTTP {error.code}). 채널 확인 후 재실행하세요.") from None
        except (URLError, TimeoutError, ConnectionError, json.JSONDecodeError, UnicodeError):
            raise ReportError("Discord 응답을 확인하지 못했습니다. 중복 방지를 위해 재시도하지 않았습니다. 채널을 확인하세요.") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=".github/study-members.json")
    parser.add_argument("--date", default=os.getenv("REPORT_DATE", "").strip())
    parser.add_argument("--dry-run", action="store_true", default=os.getenv("DRY_RUN", "false").lower() == "true")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        day, start, end = report_window(args.date)
        repository = os.getenv("GITHUB_REPOSITORY", "")
        webhook = os.getenv("DISCORD_WEBHOOK_URL", "")
        if not args.dry_run:
            discord_url(webhook)
        activities = fetch_activities(repository, os.getenv("GITHUB_TOKEN", ""), start, end, config["branch"])
        content = render_message(config, activities, day, repository)
        print(content)
        if summary_path := os.getenv("GITHUB_STEP_SUMMARY"):
            with open(summary_path, "a", encoding="utf-8") as summary:
                summary.write("## Discord 발송 내용 미리보기\n\n" + content + "\n")
        if not args.dry_run:
            message_id = post_discord(webhook, content)
            print(f"Discord message_id: {message_id}")
        print("미리보기 완료: Discord에 발송하지 않았습니다." if args.dry_run else "Discord 발송을 확인했습니다.")
        return 0
    except (ReportError, OSError) as error:
        print(f"오류: {error}" if isinstance(error, ReportError) else "오류: 로컬 파일을 읽거나 쓰지 못했습니다.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
