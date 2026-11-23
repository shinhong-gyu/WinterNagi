# WinterNagi 일일 Push 요약 설정

원하는 문제를 자유롭게 풀고 올리는 스터디를 위한 일일 기록입니다. 등록된 멤버를 **Push 기록 있는 멤버 / Push 기록 없는 멤버**로 나눠 디스코드 텍스트 채널에 게시합니다. 자동 멘션, 벌점, 순위는 없습니다.

## 기본 동작

| 항목 | 설정 |
| --- | --- |
| 발송 예정 시각 | 매일 한국 시간 오전 0시 17분 |
| 집계 날짜 | 발송일의 전날 00:00:00 이상, 다음 날 00:00:00 미만 |
| 기본 대상 | `WinterNagi`의 `main` 브랜치에서 발생한 일반 Push 및 force push |
| 멤버 판별 | 실제 활동을 실행한 GitHub 계정과 등록된 `github` 값 비교 |
| 데이터 | GitHub Repository Activity API의 활동 시각과 계정 |
| 파일 범위 | 모든 파일. README만 바꾼 Push도 포함 |
| 기본 제외 | 다른 브랜치, 태그, PR 병합, 브랜치 생성/삭제, 미등록 계정 |
| 수동 실행 | 지난 날짜 선택 가능. 기본은 발송 없는 미리보기 |
| 읽기 권한 | 자동 제공되는 `GITHUB_TOKEN`의 `contents: read` |

예를 들어 **11월 23일 전체 기록을 11월 24일 오전 0시 17분에** 발송합니다. 23시대에 보내면 그 이후의 Push가 빠지므로, 하루가 끝난 뒤 집계합니다. 이 기록은 백준 정답 여부나 풀이 개수를 판정하지 않습니다.

## 1. 파일 배치

압축 안의 `.github` 폴더와 이 설명 파일을 저장소 최상위, 즉 현재 `F:\WinterNagi\WinterNagi`에 복사합니다. 기존 `.github` 폴더가 있으면 아래 파일만 추가합니다.

| 파일 | 역할 |
| --- | --- |
| `.github/workflows/daily-discord.yml` | 매일 실행하는 GitHub Actions 설정 |
| `.github/scripts/daily_discord.py` | 활동 조회, 멤버 분류, 디스코드 메시지 작성 및 전송 |
| `.github/study-members.json` | 스터디원 명단과 집계 범위 |
| `DISCORD_DAILY_SETUP.md` | 이 안내문 |

`WinterNagi.sln`, 기존 C++ 소스, `.gitignore`를 변경할 필요는 없습니다. GitHub Actions에서 Python을 실행하므로 Windows PC에 Python을 설치할 필요도 없습니다.

## 2. 실제 멤버 명단 입력

`.github/study-members.json`에는 현재 대화에서 확인된 `shinhong-gyu`만 들어 있습니다. **나머지 실제 스터디원 3~5명의 GitHub ID와 표시 이름을 추가한 다음 업로드하세요.** 자동으로 저장소 기여자 목록을 명단으로 쓰지 않습니다. 아직 한 번도 Push하지 않은 멤버도 보고서에 포함되어야 하기 때문입니다.

아래 `replace-with-member-id`는 입력 형식 설명을 위한 예시입니다. 실제 파일에는 실제 ID를 넣습니다.

```json
{
  "branch": "main",
  "activity_types": ["push", "force_push"],
  "members": [
    {"github": "shinhong-gyu", "name": "홍규"},
    {"github": "replace-with-member-id", "name": "스터디원 이름"}
  ]
}
```

- `github`: GitHub 프로필 주소의 계정 ID. 이메일이나 `git config user.name`이 아닙니다.
- `name`: 디스코드 요약에서 보여 줄 이름 또는 닉네임입니다.
- JSON에는 주석이나 마지막 항목 뒤의 쉼표를 넣지 않습니다. UTF-8로 저장하세요.
- GitHub ID는 대소문자 구분 없이 비교하고, 명단 순서대로 표시합니다.
- 과거 날짜를 재집계할 때도 현재 명단을 사용합니다. 가입·탈퇴 이력을 별도로 보관하지 않습니다.

## 3. Discord 웹훅을 Actions Secret에 등록

디스코드에서 **서버 설정 → 연동 → 웹훅**으로 들어가 일반 텍스트 채널용 웹훅 URL을 복사합니다.

GitHub의 `WinterNagi`에서 다음으로 들어갑니다.

**Settings → Secrets and variables → Actions → New repository secret**

| 항목 | 값 |
| --- | --- |
| Name | `DISCORD_WEBHOOK_URL` |
| Secret | 디스코드에서 복사한 원래 웹훅 URL |

```text
https://discord.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN
```

**이번에는 `/github`를 붙이지 않습니다.** 앞서 설정한 GitHub → Discord 즉시 알림은 GitHub 원본 이벤트를 보내는 방식이라 `/github`가 필요했습니다. 이 스크립트는 이미 완성한 Discord JSON 메시지를 보내므로 원래 주소를 씁니다. 같은 웹훅을 쓸 경우 GitHub Webhooks 설정에는 `/github`가 붙은 주소, Actions Secret에는 붙지 않은 주소를 각각 등록하면 됩니다.

웹훅 주소를 파일이나 커밋에 넣지 마세요. Secret은 로그에서 가려지고, 스크립트도 전송 오류에 전체 URL을 출력하지 않습니다. 일반 텍스트 채널용 구성으로, 포럼·미디어 채널의 스레드 생성은 지원하지 않습니다.

## 4. 파일을 main에 업로드

초기 Git 연결과 이전 병합 충돌이 해결된 저장소에서 실행합니다. 다른 미커밋 변경이 있다면 먼저 따로 정리합니다.

```powershell
cd F:\WinterNagi\WinterNagi
git switch main
git add .github/workflows/daily-discord.yml .github/scripts/daily_discord.py .github/study-members.json DISCORD_DAILY_SETUP.md
git commit -m "Add daily Discord push summary"
git pull --rebase origin main
git push origin main
```

예약 실행은 저장소의 **기본 브랜치**에 workflow가 있어야 작동합니다. 이 저장소에서는 `main`을 기본 브랜치로 사용하는 구성을 전제로 합니다. 워크플로를 기본 브랜치에 올리고 Secret을 등록하면 다음 예약 시각부터 실제 발송이 시작됩니다.

파일을 올리기만 하고 예약 발송은 아직 시작하고 싶지 않다면 Secret을 나중에 등록하거나, Actions 화면에서 워크플로를 비활성화해 두세요. Secret 없이 예약 실행되면 발송 단계는 오류로 종료됩니다.

## 5. 먼저 미리보기로 확인

1. GitHub **Actions → Daily Discord Summary → Run workflow**를 엽니다.
2. 브랜치는 `main`을 선택합니다.
3. `report_date`는 비워 두면 한국 시간 어제입니다. 직접 지정할 때는 `YYYY-MM-DD`로 입력합니다.
4. `dry_run`을 체크한 상태로 실행합니다.
5. 실행 결과의 **Summary**에서 보고서 내용을 확인합니다. 이 실행은 디스코드에 전송하지 않습니다.
6. 실제 발송을 시험하려면 같은 화면에서 `dry_run`을 해제한 뒤 실행합니다.

아직 끝나지 않은 오늘과 미래 날짜는 거절합니다. 수동 재집계는 최근 30일 이내의 완료된 날짜만 허용합니다. 이 30일은 스크립트의 운영상 제한이며, GitHub Activity API가 30일 보관을 보장한다는 뜻은 아닙니다.

같은 날짜에 발송 모드로 다시 실행하면 같은 날짜의 메시지가 다시 올라갑니다. 발송 확인용 메시지 ID는 Actions 로그에 남습니다. 시간 초과나 네트워크 오류가 나면 이미 메시지가 도착했을 수도 있으므로 디스코드를 확인한 뒤 재실행하세요.

## 집계 기준과 변경 방법

### 일반 Push, force push, PR 병합

기본값 `"activity_types": ["push", "force_push"]`는 `main`의 일반 Push와 force push 활동을 포함합니다. force push를 하도록 권하는 설정은 아니며, 발생한 기록을 놓치지 않기 위한 분류입니다.

PR 병합은 GitHub가 별도 `pr_merge` 활동으로 기록합니다. PR 병합까지 포함하려면 다음처럼 바꿀 수 있습니다.

```json
"activity_types": ["push", "force_push", "pr_merge"]
```

이때는 PR 작성자가 아니라 **병합을 실행한 계정**으로 집계됩니다. GitHub의 merge queue를 사용하는 경우 `merge_queue_merge`는 별도 활동이며, 봇 계정으로 기록될 수 있습니다. 자유롭게 직접 Push하는 현재 스터디에는 기본값을 추천합니다.

### 모든 브랜치

`"branch": ""`로 바꾸면 모든 브랜치의 선택한 활동 유형을 조회합니다. 새 브랜치를 처음 올리는 활동도 포함하려면 `activity_types`에 `branch_creation`을 추가해야 합니다. 브랜치 생성만으로도 기록에 잡히므로, 풀이 업로드와 동일한 의미는 아닙니다. 태그 활동은 대상에서 제외합니다.

### 발송 시각

`.github/workflows/daily-discord.yml`의 다음 부분을 바꿉니다.

```yaml
schedule:
  - cron: "17 0 * * *"
    timezone: "Asia/Seoul"
```

예를 들어 `"17 9 * * *"`는 한국 시간 오전 9시 17분입니다. 시각을 바꾸어도 **한국 시간 전날의 전체 기록**을 집계합니다. 현재 GitHub Actions는 IANA 시간대 설정을 지원합니다.

## 정확성과 운영상 한계

- GitHub가 기록한 **활동 실행자와 활동 발생 시각**을 씁니다. 커밋 작성자나 커밋 작성일로 Push 여부를 추정하지 않습니다. 예전에 만든 커밋을 오늘 Push하면 오늘 활동에 포함됩니다.
- 선택한 브랜치와 활동 유형 안에서, 등록된 계정에 한 번이라도 기록이 있으면 해당 멤버를 첫 번째 그룹에 표시합니다. README만 수정한 Push도 포함되며, 파일명이나 백준 정답 여부는 검사하지 않습니다.
- 활동 목록은 첫 100개에서 자르지 않고 다음 페이지를 조회합니다. 한국 시간 하루의 시작보다 과거 기록에 도달하거나 페이지가 끝날 때까지 확인합니다.
- API 실패, 잘못된 응답, 순서 이상, 반복되는 페이지, 방어적 조회 상한 초과, 해당 기간의 계정 식별 불가 활동이 있으면 일반 보고서를 발송하지 않고 실패합니다. 오류를 '전원 기록 없음'으로 바꾸지 않습니다.
- GitHub는 이 활동 API의 즉시 반영이나 무제한 보관을 보장한다고 명시하지 않습니다. 따라서 'Push 기록 없음'은 **조회 시점에 해당 범위에서 확인된 기록이 없음**이라는 뜻입니다.
- 예약은 지정 시각보다 늦어질 수 있고, 부하가 심하면 건너뛸 수 있습니다. 놓친 날은 날짜를 지정해 수동 실행할 수 있습니다. 하루 이상 지연된 실행은 시작 시점 기준 전날을 기본값으로 사용하므로, 원래 의도한 날짜는 수동으로 지정합니다.
- 공개 저장소에서 60일간 저장소 활동이 없으면 예약 워크플로가 자동으로 비활성화될 수 있습니다.
- 이 설정은 채널 메시지를 게시합니다. 휴대폰·PC 알림은 각 멤버의 Discord 알림 설정을 따릅니다.

## 오류 확인

| 증상 | 확인할 것 |
| --- | --- |
| 워크플로가 안 보임 | 파일 경로와 기본 브랜치, 저장소 Actions 활성화 여부 |
| 수동 실행이 건너뛰어짐 | Run workflow에서 기본 브랜치를 선택했는지 |
| 웹훅 URL 오류 | Secret 이름, URL 끝의 `/github` 제거, 일반 텍스트 채널 여부 |
| GitHub API 401/403 | workflow의 `permissions: contents: read`, 저장소 정책 |
| GitHub API 404 | 저장소 이름 변경 또는 접근 권한 |
| 명단에 특정 멤버가 없음 | `study-members.json`의 실제 GitHub ID와 이름 |
| Push했지만 기록 없음 | 해당 날짜의 한국 시간 경계, `main` 여부, PR 병합 여부 |
| 중복 메시지 | 같은 날짜의 수동 실행·재실행 여부 |

## 공식 참고 자료

- [GitHub Repository Activity API](https://docs.github.com/en/rest/repos/repos#list-repository-activities)
- [Repository activity와 인증된 사용자](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/using-the-activity-view-to-see-changes-to-a-repository)
- [GitHub Actions 예약 문법과 시간대](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule)
- [예약 실행 지연·기본 브랜치·비활성화 조건](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [Discord 웹훅 전송](https://docs.discord.com/developers/resources/webhook#execute-webhook)

이 묶음은 설정 파일을 제공하며, 저장소 업로드나 디스코드 발송을 대신 실행한 상태는 아닙니다. 설치 전에 실제 명단을 채우고 Actions의 미리보기로 확인하세요.
