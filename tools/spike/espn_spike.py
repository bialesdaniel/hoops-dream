#!/usr/bin/env python3
"""ESPN Fantasy Basketball feasibility spike (read-only, Python 3.9+ standard library only).

Question it answers: can ESPN alone feed the app (per-game stats for any date range, rosters,
league settings, NBA schedule, player birthdates)?

Usage:
  python3 espn_spike.py --league-id 123456
  # Private league: pass cookies via environment variables, never as arguments:
  ESPN_S2='AE...' ESPN_SWID='{XXXXXXXX-XXXX-...}' python3 espn_spike.py --league-id 123456

Outputs, in ./espn_spike_out/<UTC timestamp>/:
  report.md       Redacted summary. Safe to paste back into the chat. Contains no cookies
                  and no league-member names.
  raw/<label>.json.gz
                  Raw responses, usable as test fixtures. SWIDs (ESPN member ids, which are
                  half of a login cookie) are replaced on write with consistent fake GUIDs.
                  Team and display names remain, so keep the files in a private repo.
  raw/meta.json   Replay metadata: league_id, season, captured_at, latest scoring period.

The script sends at most ~1 request/second and roughly 20-60 requests in total.
"""

import argparse
import datetime as dt
import gzip
import json
import os
import re
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request

VERSION = "1.1"
SWID_RE = re.compile(rb"\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}")
API = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/{season}"
CORE_ATHLETE = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/athletes/{pid}"
UA = "Mozilla/5.0 (X11; Linux x86_64) espn-feasibility-spike/" + VERSION

SLOT_NAMES = {0: "PG", 1: "SG", 2: "SF", 3: "PF", 4: "C", 5: "G", 6: "F", 7: "SG/SF",
              8: "G/F", 9: "PF/C", 10: "F/C", 11: "UTIL", 12: "BE", 13: "IR", 14: "slot14",
              15: "Rookie", 16: "slot16", 17: "slot17"}
# The sheet's FPTS = FGM - FGA + FTM - FTA + REB + AST + STL + BLK - TOV + PTS
SHEET_WEIGHTS = {13: 1, 14: -1, 15: 1, 16: -1, 6: 1, 3: 1, 2: 1, 1: 1, 11: -1, 0: 1}
STAT_NAMES = {0: "PTS", 1: "BLK", 2: "STL", 3: "AST", 4: "OREB", 5: "DREB", 6: "REB",
              11: "TO", 13: "FGM", 14: "FGA", 15: "FTM", 16: "FTA", 17: "3PM", 18: "3PA",
              40: "MIN", 41: "stat41", 42: "stat42"}
AGG_PREFIXES = ("00", "10", "01", "02", "03")  # season total, projected, last 7/15/30 days


def et(ms):
  """Format epoch millis as US/Eastern (falls back to UTC)."""
  if not ms:
    return "n/a"
  t = dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc)
  try:
    from zoneinfo import ZoneInfo  # pylint: disable=import-outside-toplevel
    return t.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M %Z")
  except Exception:  # pylint: disable=broad-except
    return t.strftime("%Y-%m-%d %H:%M UTC")


def et_date(ms):
  return et(ms)[:10]


def is_per_game(split):
  if split.get("statSplitTypeId") == 5:
    return True
  sid = str(split.get("id", ""))
  return sid[:2] not in AGG_PREFIXES and (split.get("scoringPeriodId") or 0) > 0


class Spike:
  """Runs the checks and builds a redacted Markdown report."""

  def __init__(self, args, out_dir):
    self.season = args.season
    self.league_id = args.league_id
    self.fa_sample = args.fa_sample
    self.base = API.format(season=args.season)
    self.league_url = f"{self.base}/segments/0/leagues/{args.league_id}"
    s2, swid = os.environ.get("ESPN_S2"), os.environ.get("ESPN_SWID")
    self.cookie = f"espn_s2={s2}; SWID={swid}" if s2 and swid else None
    self.use_cookie = False
    self.out_dir = out_dir
    self.raw_dir = os.path.join(out_dir, "raw")
    os.makedirs(self.raw_dir, exist_ok=True)
    self.calls = []
    self.lines = []
    self.verdict = {}
    self.status = {}
    self.access = "unknown"
    self.swid_map = {}

  # ---------------------------------------------------------------- plumbing
  def say(self, line=""):
    self.lines.append(line)

  def scrub(self, body):
    """Replaces every SWID-shaped GUID with a consistent fake GUID."""
    def repl(m):
      fake = self.swid_map.setdefault(
          m.group(0), "{00000000-0000-0000-0000-%012d}" % (len(self.swid_map) + 1))
      return fake.encode()
    return SWID_RE.sub(repl, body)

  def get(self, url, label, params=None, fantasy_filter=None, cookie=None):
    """GET JSON. Saves the raw body (gzipped) on HTTP 200. Returns (status, data)."""
    use_cookie = self.use_cookie if cookie is None else cookie
    if params:
      url += "?" + urllib.parse.urlencode(params, doseq=True)
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if fantasy_filter is not None:
      headers["x-fantasy-filter"] = json.dumps(fantasy_filter)
    sent_cookie = bool(use_cookie and self.cookie)
    if sent_cookie:
      headers["Cookie"] = self.cookie
    time.sleep(1.0)  # politeness: at most ~1 request per second
    t0 = time.monotonic()
    status, body = None, b""
    try:
      with urllib.request.urlopen(urllib.request.Request(url, headers=headers),
                                  timeout=60) as resp:
        status, body = resp.status, resp.read()
    except urllib.error.HTTPError as e:
      status, body = e.code, e.read()
    except Exception as e:  # pylint: disable=broad-except
      status = f"ERR {type(e).__name__}"
    ms = int((time.monotonic() - t0) * 1000)
    self.calls.append((label, status, ms, len(body), sent_cookie))
    data = None
    if status == 200:
      with gzip.open(os.path.join(self.raw_dir, f"{label}.json.gz"), "wb") as f:
        f.write(self.scrub(body))
      try:
        data = json.loads(body)
      except ValueError:
        data = None
    return status, data

  def safe(self, fn, *a):
    try:
      return fn(*a)
    except Exception:  # pylint: disable=broad-except
      self.say(f"- ⚠️ `{fn.__name__}` crashed (please paste this):")
      self.say("```\n" + traceback.format_exc()[-1500:] + "```")
      return None

  # ------------------------------------------------------------------ checks
  def check_access(self):
    s, d = self.get(self.league_url, "league_settings_nocookie", {"view": "mSettings"},
                    cookie=False)
    if s == 200:
      self.access = "PUBLIC: works without cookies"
      self.verdict["League access"] = "PUBLIC (no secret needed)"
      return d
    if self.cookie:
      s2, d2 = self.get(self.league_url, "league_settings", {"view": "mSettings"}, cookie=True)
      if s2 == 200:
        self.use_cookie = True
        self.access = f"PRIVATE: no-cookie status {s}; cookies work"
        self.verdict["League access"] = "PRIVATE (cookies required)"
        return d2
      self.access = f"FAIL: no-cookie status {s}, with-cookie status {s2}"
    else:
      self.access = f"PRIVATE (status {s}): set ESPN_S2 and ESPN_SWID and re-run"
    self.verdict["League access"] = self.access
    return None

  def check_schedule(self):
    s, d = self.get(self.base, "pro_team_schedules_nocookie", {"view": "proTeamSchedules_wl"},
                    cookie=False)
    if s != 200 or not d:
      self.say(f"- NBA schedule: FAIL (status {s})")
      self.verdict["NBA schedule"] = f"FAIL ({s})"
      return {}
    teams = [t for t in d.get("settings", {}).get("proTeams", []) if t.get("id")]
    sched = {t["id"]: t.get("proGamesByScoringPeriod", {}) or {} for t in teams}
    per_team = [sum(len(g) for g in s_.values()) for s_ in sched.values()] or [0]
    sp_dates, official, past = {}, 0, 0
    now_ms = time.time() * 1000
    for games_by_sp in sched.values():
      for sp, games in games_by_sp.items():
        for g in games:
          sp_dates.setdefault(int(sp), set()).add(et_date(g.get("date")))
          if g.get("date", 0) < now_ms - 6 * 3600 * 1000:
            past += 1
            official += 1 if g.get("statsOfficial") else 0
    sps = sorted(sp_dates)
    multi = [sp for sp, ds in sp_dates.items() if len(ds) > 1]
    self.say(f"- NBA schedule (no cookies): {len(teams)} teams; games per team "
             f"{min(per_team)}–{max(per_team)}; scoring periods {sps[0] if sps else '?'}–"
             f"{sps[-1] if sps else '?'}")
    if sps:
      self.say(f"- Scoring period 1 = {sorted(sp_dates[sps[0]])}; periods spanning more than "
               f"one US/Eastern date: {len(multi)} {multi[:5]}")
    self.say(f"- `statsOfficial` flag on past games: {official}/{past} (in team-game rows)")
    self.verdict["NBA schedule"] = "PASS" if min(per_team) >= 80 else f"CHECK ({min(per_team)} min games)"
    return sched

  def check_players_wl(self):
    s, d = self.get(f"{self.base}/players", "players_wl_nocookie", {"view": "players_wl"},
                    {"filterActive": {"value": True}}, cookie=False)
    if s != 200 or not isinstance(d, list):
      self.say(f"- Active NBA players list (no cookies): FAIL (status {s})")
      return []
    self.say(f"- Active NBA players list (no cookies): {len(d)} players")
    return [p.get("id") for p in d if p.get("id")]

  def check_settings(self, d):
    st, self.status = d.get("settings", {}), d.get("status", {})
    status = self.status
    self.say(f"- Status: first scoring period {status.get('firstScoringPeriod')}, latest "
             f"{status.get('latestScoringPeriod')}, final {status.get('finalScoringPeriod')}, "
             f"current matchup period {status.get('currentMatchupPeriod')}")
    sc = st.get("scoringSettings", {})
    espn_w, overrides = {}, 0
    for it in sc.get("scoringItems", []):
      espn_w[int(it.get("statId"))] = it.get("points", 0) or 0
      overrides += 1 if it.get("pointsOverrides") else 0
    diffs = [f"{STAT_NAMES.get(k, k)}: ESPN {espn_w.get(k, 0)} vs sheet {SHEET_WEIGHTS.get(k, 0)}"
             for k in sorted(set(espn_w) | set(SHEET_WEIGHTS))
             if abs(espn_w.get(k, 0) - SHEET_WEIGHTS.get(k, 0)) > 1e-9]
    ok = not diffs
    self.say(f"- Scoring type {sc.get('scoringType')}; weights vs sheet FPTS: "
             + ("PASS (identical)" if ok else "DIFF: " + "; ".join(diffs))
             + (f"; {overrides} items have per-slot overrides" if overrides else ""))
    self.verdict["Scoring == sheet FPTS"] = "PASS" if ok else "DIFF (see §3)"
    rs = st.get("rosterSettings", {})
    counts = rs.get("lineupSlotCounts", {}) or {}
    slots = ", ".join(f"{SLOT_NAMES.get(int(k), 'slot' + str(k))}×{v}"
                      for k, v in sorted(counts.items(), key=lambda kv: int(kv[0])) if v)
    self.say(f"- Lineup slots: {slots} (total {sum(v for v in counts.values() if v)}); "
             f"lineup lock: {rs.get('lineupLocktimeType')}")
    ss = st.get("scheduleSettings", {})
    mps = ss.get("matchupPeriods", {}) or {}
    longp = sorted(((int(k), v) for k, v in mps.items() if len(v) > 7))
    self.say(f"- Matchup periods: {len(mps)} (regular season {ss.get('matchupPeriodCount')}); "
             f"playoff teams {ss.get('playoffTeamCount')}; playoff matchup length "
             f"{ss.get('playoffMatchupPeriodLength')}; divisions {len(ss.get('divisions', []))}")
    for k, v in longp:
      self.say(f"  - Matchup period {k} spans scoring periods {v[0]}–{v[-1]} ({len(v)} days)")
    tr = st.get("tradeSettings", {})
    self.say(f"- Trade deadline: {et(tr.get('deadlineDate'))}; veto votes "
             f"{tr.get('vetoVotesRequired')}; review hours {tr.get('revisionHours')}")
    self.verdict["Trade deadline"] = et(tr.get("deadlineDate"))
    dr = st.get("draftSettings", {})
    self.say(f"- Draft: type {dr.get('type')}; keeper count {dr.get('keeperCount')}; "
             f"date {et(dr.get('date'))}")
    acq = st.get("acquisitionSettings", {})
    self.say(f"- Acquisitions: limit {acq.get('acquisitionLimit')}; matchup limit "
             f"{acq.get('matchupAcquisitionLimit')}; waiver hours {acq.get('waiverHours')}")

  def check_rosters(self):
    s, d = self.get(self.league_url, "league_team_roster", {"view": ["mTeam", "mRoster"]})
    if s != 200 or not d:
      self.say(f"- Rosters: FAIL (status {s})")
      return []
    teams, sizes, slot_use, rostered = d.get("teams", []), [], {}, []
    for t in teams:
      entries = t.get("roster", {}).get("entries", [])
      sizes.append(len(entries))
      for e in entries:
        slot_use[e.get("lineupSlotId")] = slot_use.get(e.get("lineupSlotId"), 0) + 1
        rostered.append(e.get("playerId"))
    self.say(f"- Teams {len(teams)}; roster sizes {min(sizes or [0])}–{max(sizes or [0])}; "
             f"members {len(d.get('members', []))}")
    self.say("- Rostered players by lineup slot: " + ", ".join(
        f"{SLOT_NAMES.get(k, k)}={v}" for k, v in sorted(slot_use.items(), key=lambda kv: kv[0] or 0)))
    return rostered

  def check_historical_rosters(self, current):
    first = self.status.get("firstScoringPeriod") or 1
    s, d = self.get(self.league_url, "league_roster_first_sp",
                    {"view": "mRoster", "scoringPeriodId": first})
    if s != 200 or not d:
      self.say(f"- Past rosters: FAIL (status {s})")
      self.verdict["Past rosters"] = f"FAIL ({s})"
      return
    past = {e.get("playerId") for t in d.get("teams", [])
            for e in t.get("roster", {}).get("entries", [])}
    diff = len(past ^ set(current))
    if diff:
      self.say(f"- Past rosters: PASS (roster at scoring period {first} differs from today by "
               f"{diff} players)")
      self.verdict["Past rosters"] = "PASS"
    else:
      self.say(f"- Past rosters: INCONCLUSIVE (roster at scoring period {first} matches today; "
               "either no moves yet or ESPN ignores scoringPeriodId)")
      self.verdict["Past rosters"] = "INCONCLUSIVE: start daily capture to be safe"

  def check_pool(self):
    filt = {"players": {"filterStatus": {"value": ["FREEAGENT", "WAIVERS", "ONTEAM"]},
                        "limit": 2000, "sortPercOwned": {"sortPriority": 1, "sortAsc": False}}}
    s, d = self.get(self.league_url, "player_pool", {
        "view": "kona_player_info",
        "scoringPeriodId": self.status.get("latestScoringPeriod") or 1}, filt)
    if s != 200 or not d:
      self.say(f"- Player pool: FAIL (status {s})")
      return [], []
    players = d.get("players", [])
    inj = sum(1 for p in players if "injuryStatus" in (p.get("player") or {}))
    fa = [p.get("id") for p in players if p.get("status") in ("FREEAGENT", "WAIVERS")]
    self.say(f"- Player pool: {len(players)} players ({len(fa)} free agents/waivers); "
             f"injuryStatus present on {inj}")
    return [p.get("id") for p in players], fa

  def check_per_game(self, ids, sched):
    latest = self.status.get("latestScoringPeriod") or 1
    first = self.status.get("firstScoringPeriod") or 1
    yr, got = str(self.season), {}
    for i in range(0, len(ids), 50):
      filt = {"players": {"filterIds": {"value": ids[i:i + 50]},
                          "filterStatsForTopScoringPeriodIds": {
                              "value": latest, "additionalValue": ["00" + yr, "10" + yr]}}}
      s, d = self.get(self.league_url, f"playercard_{i // 50:02d}",
                      {"view": "kona_playercard"}, filt)
      if s != 200 or not d:
        self.say(f"- kona_playercard batch {i // 50}: FAIL (status {s})")
        continue
      for p in d.get("players", []):
        pl = p.get("player") or {}
        got[pl.get("id")] = pl
    games = with_games = oracle_n = oracle_ok = cov_num = cov_den = 0
    earliest, votes = None, {41: 0, 42: 0}
    keys_seen = set()
    for pl in got.values():
      per_game = [s_ for s_ in pl.get("stats", []) if s_.get("seasonId") == self.season
                  and s_.get("statSourceId") == 0 and is_per_game(s_)]
      with_games += 1 if per_game else 0
      games += len(per_game)
      have = set()
      for sp in per_game:
        spid = int(sp.get("scoringPeriodId") or 0)
        have.add(spid)
        earliest = spid if earliest is None else min(earliest, spid)
        st = {int(k): v for k, v in (sp.get("stats") or {}).items()}
        keys_seen.update(st)
        if st:
          oracle_n += 1
          fpts = sum(w * st.get(k, 0) for k, w in SHEET_WEIGHTS.items())
          oracle_ok += 1 if abs(fpts - (sp.get("appliedTotal") or 0)) < 0.01 else 0
          if st.get(40, 0) > 0:  # played minutes: games played must be 1, so a 0 means "started"
            for k in (41, 42):
              votes[k] += 1 if st.get(k) == 0 else 0
      team_sps = {int(x) for x in sched.get(pl.get("proTeamId"), {}) if int(x) <= latest}
      cov_den += len(team_sps)
      cov_num += len(have & team_sps)
    self.say(f"- Per-game box scores: {len(got)} players fetched; {with_games} have game lines; "
             f"{games} game lines total; earliest scoring period {earliest} (season starts at "
             f"{first})")
    if cov_den:
      self.say(f"- Coverage: game lines on {cov_num}/{cov_den} team game days "
               f"({100 * cov_num / cov_den:.0f}%; DNPs and injuries lower this)")
    if oracle_n:
      self.say(f"- FPTS oracle: the sheet's formula reproduces ESPN appliedTotal on "
               f"{oracle_ok}/{oracle_n} game lines ({100 * oracle_ok / oracle_n:.1f}%)")
    gs = max(votes, key=votes.get) if any(votes.values()) else None
    self.say(f"- Stat-ID check: bench appearances with a 0 → stat41 {votes[41]}, stat42 "
             f"{votes[42]} ⇒ games started (GS) is probably stat{gs}" if gs else
             "- Stat-ID check (GS vs GP): inconclusive")
    self.say(f"- Stat keys seen: {sorted(keys_seen)}")
    self.verdict["Per-game stats"] = (
        f"PASS (backfill from scoring period {earliest})" if games and earliest == first
        else ("PARTIAL" if games else "FAIL"))
    if oracle_n:
      self.verdict["FPTS oracle"] = f"{100 * oracle_ok / oracle_n:.1f}% match"

  def check_leaguedefaults(self, ids):
    latest = self.status.get("latestScoringPeriod") or 30
    yr = str(self.season)
    filt = {"players": {"filterIds": {"value": ids[:5]},
                        "filterStatsForTopScoringPeriodIds": {
                            "value": latest, "additionalValue": ["00" + yr]}}}
    s, d = self.get(f"{self.base}/segments/0/leaguedefaults/3", "leaguedefaults_nocookie",
                    {"view": "kona_playercard"}, filt, cookie=False)
    n = sum(1 for p in (d or {}).get("players", [])
            for sp in (p.get("player") or {}).get("stats", []) if is_per_game(sp))
    res = (f"PASS ({n} game lines for 5 players)" if s == 200 and n
           else f"NO ({'status ' + str(s) if s != 200 else 'no per-game lines'})")
    self.say(f"- Per-game stats WITHOUT cookies (leaguedefaults endpoint): {res}")
    self.verdict["Stats without cookies"] = res

  def check_dob(self, ids):
    rows, ok = [], 0
    for pid in ids[:5]:
      s, d = self.get(CORE_ATHLETE.format(pid=pid), f"core_athlete_{pid}", cookie=False)
      d = d or {}
      ok += 1 if d.get("dateOfBirth") else 0
      rows.append(f"{d.get('displayName', pid)}: dateOfBirth={d.get('dateOfBirth', '—')}, "
                  f"age={d.get('age', '—')}, experience={(d.get('experience') or {}).get('years', '—')} "
                  f"(status {s})")
    self.say(f"- Birthdates via ESPN core athletes API (no cookies): {ok}/{len(rows)}")
    for r in rows:
      self.say(f"  - {r}")
    self.verdict["Birthdates"] = f"{ok}/{len(rows)}"

  def check_prior_season(self):
    prev = self.season - 1
    s, _ = self.get(f"{API.format(season=prev)}/segments/0/leagues/{self.league_id}",
                    f"prior_season_{prev}", {"view": "mSettings"})
    self.say(f"- Prior season ({prev}) league data: {'PASS' if s == 200 else f'FAIL (status {s})'}")
    self.verdict["Prior season"] = "PASS" if s == 200 else f"FAIL ({s})"

  # --------------------------------------------------------------------- run
  def run(self):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    self.say(f"# ESPN feasibility spike v{VERSION}: season {self.season}, run {now}")
    self.say(f"Cookies provided: {'yes' if self.cookie else 'no'} (values are never printed)")
    self.say("\n## 1. Access")
    settings = self.safe(self.check_access)
    self.say(f"- League: {self.access}")
    self.say("\n## 2. League-independent data")
    sched = self.safe(self.check_schedule) or {}
    nba_ids = self.safe(self.check_players_wl) or []
    sample_ids = nba_ids
    if settings:
      self.say("\n## 3. League settings")
      self.safe(self.check_settings, settings)
      self.say("\n## 4. Rosters and player pool")
      rostered = self.safe(self.check_rosters) or []
      self.safe(self.check_historical_rosters, rostered)
      pool = self.safe(self.check_pool) or ([], [])
      fas = [p for p in pool[1] if p not in set(rostered)]
      if self.fa_sample > 0:
        fas = fas[: self.fa_sample]
      self.say("\n## 5. Per-game stats")
      self.safe(self.check_per_game, rostered + fas, sched)
      self.safe(self.check_prior_season)
      sample_ids = (rostered[:3] + pool[1][-2:]) or nba_ids
    else:
      self.say("\n## 3–5. League-specific checks skipped (no league access)")
    self.say("\n## 6. Cookie-free fallbacks")
    if sample_ids:
      self.safe(self.check_leaguedefaults, sample_ids)
      self.safe(self.check_dob, sample_ids)
    self.say("\n## 7. Verdict")
    for k, v in self.verdict.items():
      self.say(f"- **{k}:** {v}")
    self.say("\n## 8. Request log (≤1 request/second)")
    self.say("| # | request | status | ms | KB | cookie |")
    self.say("|---|---|---|---|---|---|")
    for i, (label, status, ms, size, ck) in enumerate(self.calls, 1):
      self.say(f"| {i} | {label} | {status} | {ms} | {size // 1024} | {'y' if ck else 'n'} |")
    report = "\n".join(self.lines) + "\n"
    with open(os.path.join(self.out_dir, "report.md"), "w", encoding="utf-8") as f:
      f.write(report)
    meta = {"league_id": self.league_id, "season": self.season,
            "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "latest_scoring_period": self.status.get("latestScoringPeriod"),
            "first_scoring_period": self.status.get("firstScoringPeriod"),
            "spike_version": VERSION, "swids_scrubbed": len(self.swid_map)}
    with open(os.path.join(self.raw_dir, "meta.json"), "w", encoding="utf-8") as f:
      json.dump(meta, f, indent=2)
    print(report)
    print(f"Report: {os.path.join(self.out_dir, 'report.md')}")
    print(f"Raw responses (keep private): {self.raw_dir}")


def main():
  ap = argparse.ArgumentParser(description="ESPN fantasy basketball feasibility spike")
  ap.add_argument("--league-id", type=int, required=True)
  ap.add_argument("--season", type=int, default=2027, help="ESPN season year (2026-27 = 2027)")
  ap.add_argument("--out", default="espn_spike_out")
  ap.add_argument("--fa-sample", type=int, default=0,
                  help="free agents to fetch per-game stats for (0 = all, the default)")
  args = ap.parse_args()
  stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
  Spike(args, os.path.join(args.out, stamp)).run()


if __name__ == "__main__":
  main()
