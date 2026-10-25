#!/bin/bash
# Install free-research onto the host skill directories that exist on this Mac.
# macOS only: mtimes come from `stat -f`. The treg token is never printed or
# written by this script; host CLIs receive it only as an argument or by name.
set +x
set -euo pipefail
unset CDPATH

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
SKILL_SRC="$REPO_ROOT/skills/free-research"
TREG_URL="https://treg.to/mcp/"

CHECK=0
WITH_TREG=0
FORCE=0
AGENTS_DIR="$HOME/.agents/skills"
AGENTS_EXPLICIT=0
SKIPPED_ANY=0
SYMLINK_REFUSED=0

usage() {
  cat <<'EOF'
Usage: scripts/install.sh [--check] [--with-treg] [--force] [--agents-dir PATH] [--help]

Copy skills/free-research into each present host's skills directory.
A host is present when its CLI is on PATH or its config directory exists
(~/.claude, ~/.grok, ~/.codex, or ~/.gemini). Existing ~/.agents/skills
also receives a copy. The copy is real files, not a symlink.
__pycache__ and .DS_Store are skipped. A destination file newer than the
repo file is left in place unless --force.

Options:
  --agents-dir PATH
                Install for other agents in PATH, even if it does not exist.
                Default: ~/.agents/skills (used only when it exists).
                Configure treg MCP separately in each of these agents.
  --check       Print one status block per host and a next-steps list.
                Does not copy files or add MCP servers. Always exits 0.
  --with-treg   Add the treg MCP server (https://treg.to/mcp/) for each
                present host. Requires TREG_TOKEN in the environment.
                Skips a host that already has treg configured unless --force.
                Every present host is attempted; a failure on one host does
                not stop the others, and a per-host result list is printed.
                The token is not printed, logged, or written into the repo.
  --force       Overwrite newer destination files and replace treg MCP
                (runs `mcp remove treg` first when it is already configured).
  --help        Show this help.

Exit status:
  0  install finished, --check, or --help
  1  a newer destination file was kept, a destination was a symlink,
     or a treg MCP command failed
  2  unknown option
EOF
}

redact() {
  GROK_NOTES_VALUE=$(grok_notes_dir_value) awk '
    function replace_all(s, find, repl,    out, i) {
      if (find == "") {
        return s
      }
      out = ""
      while ((i = index(s, find)) > 0) {
        out = out substr(s, 1, i - 1) repl
        s = substr(s, i + length(find))
      }
      return out s
    }
    BEGIN {
      token = ENVIRON["TREG_TOKEN"]
      notes = ENVIRON["FREE_RESEARCH_NOTES_DIR"]
      grok_notes = ENVIRON["GROK_NOTES_VALUE"]
    }
    {
      line = replace_all($0, token, "***")
      line = replace_all(line, notes, "***")
      line = replace_all(line, grok_notes, "***")
      out = ""
      while ((i = index(tolower(line), "bearer ")) > 0) {
        head = substr(line, 1, i + 6)
        tail = substr(line, i + 7)
        n = length(tail)
        for (j = 1; j <= length(tail); j++) {
          c = substr(tail, j, 1)
          if (c == " " || c == "\"" || c == "\047" || c == ",") {
            n = j - 1
            break
          }
        }
        out = out head "***"
        line = substr(tail, n + 1)
      }
      print out line
    }
  '
}

host_present() {
  local cli="$1"
  local config_dir="$2"
  if command -v "$cli" >/dev/null 2>&1; then
    return 0
  fi
  if [[ -d "$HOME/$config_dir" ]]; then
    return 0
  fi
  return 1
}

# True only for a "treg" key directly inside an "mcpServers" object, not for
# the word elsewhere in a large state file such as ~/.claude.json.
json_has_treg_key() {
  awk '
    BEGIN { depth = 0; mcp_depth = 0; pending = 0; found = 0; in_string = 0 }
    {
      n = length($0)
      for (i = 1; i <= n; i++) {
        c = substr($0, i, 1)
        if (in_string) {
          if (c == "\\") {
            i++
          } else if (c == "\"") {
            in_string = 0
            last_string = current
          } else {
            current = current c
          }
          continue
        }
        if (c == "\"") {
          in_string = 1
          current = ""
        } else if (c == ":" && last_string != "") {
          if (last_string == "mcpServers") {
            pending = 1
          } else if (last_string == "treg" && mcp_depth > 0 && depth == mcp_depth) {
            found = 1
            exit 0
          }
          last_string = ""
        } else if (c == "{") {
          depth++
          if (pending) {
            mcp_depth = depth
          }
          pending = 0
        } else if (c == "}") {
          if (depth == mcp_depth) {
            mcp_depth = 0
          }
          depth--
        } else if (c != " " && c != "\t") {
          pending = 0
          last_string = ""
        }
      }
    }
    END { exit found ? 0 : 1 }
  ' "$1"
}

toml_has_treg() {
  awk '
    BEGIN { found = 0 }
    /^[[:space:]]*\[mcp_servers\.treg(\.|])/ { found = 1; exit 0 }
    END { exit found ? 0 : 1 }
  ' "$1"
}

codex_treg_token_env_var() {
  local file="$HOME/.codex/config.toml"
  [[ -f "$file" ]] || return 0
  awk '
    /^[[:space:]]*\[/ {
      treg = ($0 ~ /^[[:space:]]*\[mcp_servers\.treg\][[:space:]]*(#.*)?$/)
    }
    treg && /^[[:space:]]*bearer_token_env_var[[:space:]]*=/ {
      sub(/^[^=]*=[[:space:]]*/, "")
      quote = substr($0, 1, 1)
      if (quote != "\"" && quote != "\047") exit
      name = substr($0, 2)
      end = index(name, quote)
      if (!end) exit
      name = substr(name, 1, end - 1)
      if (name ~ /^[A-Za-z_][A-Za-z0-9_]*$/) print name
      exit
    }
  ' "$file"
}

# Prints the quoted FREE_RESEARCH_NOTES_DIR value from the Grok config, if any.
grok_notes_dir_value() {
  local file="$HOME/.grok/config.toml"
  [[ -f "$file" ]] || return 0
  awk '
    /^[[:space:]]*(FREE_RESEARCH_NOTES_DIR|"FREE_RESEARCH_NOTES_DIR"|\047FREE_RESEARCH_NOTES_DIR\047)[[:space:]]*=[[:space:]]*("[^"]|\047[^\047])/ {
      sub(/^[^=]*=[[:space:]]*/, "")
      quote = substr($0, 1, 1)
      rest = substr($0, 2)
      print substr(rest, 1, index(rest, quote) - 1)
      exit
    }
  ' "$file"
}

grok_has_notes_dir() {
  [[ -n "$(grok_notes_dir_value)" ]]
}

text_names_treg() {
  printf '%s\n' "$1" | awk '
    BEGIN { found = 0 }
    {
      n = split($0, parts, /[^A-Za-z0-9_-]+/)
      for (i = 1; i <= n; i++) {
        if (parts[i] == "treg") {
          found = 1
        }
      }
    }
    END { exit found ? 0 : 1 }
  '
}

config_has_treg() {
  local cli="$1"
  local file
  case "$cli" in
    claude)
      for file in "$HOME/.claude.json" "$HOME/.claude/mcp.json"; do
        if [[ -f "$file" ]] && json_has_treg_key "$file"; then
          return 0
        fi
      done
      ;;
    grok)
      file="$HOME/.grok/config.toml"
      if [[ -f "$file" ]] && toml_has_treg "$file"; then
        return 0
      fi
      ;;
    codex)
      file="$HOME/.codex/config.toml"
      if [[ -f "$file" ]] && toml_has_treg "$file"; then
        return 0
      fi
      ;;
    agy)
      file="$HOME/.gemini/antigravity/mcp_config.json"
      if [[ -f "$file" ]] && json_has_treg_key "$file"; then
        return 0
      fi
      ;;
  esac
  return 1
}

treg_configured() {
  local cli="$1"
  local out status
  if config_has_treg "$cli"; then
    return 0
  fi
  if ! command -v "$cli" >/dev/null 2>&1; then
    return 1
  fi
  set +e
  out=$("$cli" mcp list 2>&1 </dev/null)
  status=$?
  set -e
  if [[ "$status" -eq 0 ]] && text_names_treg "$out"; then
    return 0
  fi
  return 1
}

last30days_present() {
  local base="$1"
  local cache match
  if [[ -d "$base/skills/last30days" ]]; then
    return 0
  fi
  for cache in "$base/plugins" "$base/installed-plugins"; do
    if [[ ! -d "$cache" ]]; then
      continue
    fi
    match=$(
      find "$cache" -maxdepth 6 \
        \( -type d \( -name "last30days" -o -name "last30days-skill-*" \) \) \
        -print 2>/dev/null || true
    )
    if [[ -n "$match" ]]; then
      return 0
    fi
  done
  return 1
}

duplicate_names() {
  local dir="$HOME/.grok/installed-plugins"
  local path base
  if [[ ! -d "$dir" ]]; then
    return 0
  fi
  find "$dir" -maxdepth 1 -type d -name "free-research-skill-*" -print 2>/dev/null |
    while IFS= read -r path; do
      [[ -n "$path" ]] || continue
      base=$(basename "$path")
      printf '%s\n' "$base"
    done
}

skill_version() {
  awk '
    BEGIN { front = 0; marks = 0 }
    /^---[[:space:]]*$/ {
      marks++
      if (marks == 1) {
        front = 1
        next
      }
      exit
    }
    front && /^version:[[:space:]]*/ {
      sub(/^version:[[:space:]]*/, "")
      gsub(/["]/, "")
      gsub(/[[:space:]]/, "")
      print
      exit
    }
  ' "$1"
}

print_host_status() {
  local label="$1"
  local cli="$2"
  local config_dir="$3"
  local skill_md="$HOME/$config_dir/skills/free-research/SKILL.md"
  local version dups token_env

  printf '%s\n' "== ${label} =="
  if host_present "$cli" "$config_dir"; then
    if command -v "$cli" >/dev/null 2>&1; then
      printf '%s\n' "host: found (cli)"
    else
      printf '%s\n' "host: found (config dir)"
    fi
  else
    printf '%s\n' "host: not found"
  fi

  if [[ -f "$skill_md" ]]; then
    version=$(skill_version "$skill_md")
    if [[ -n "$version" ]]; then
      printf '%s\n' "skill: installed ${version}"
    else
      printf '%s\n' "skill: installed (version unknown)"
    fi
  else
    printf '%s\n' "skill: not installed"
  fi

  if last30days_present "$HOME/$config_dir"; then
    printf '%s\n' "last30days: present"
  else
    printf '%s\n' "last30days: missing"
  fi

  if treg_configured "$cli"; then
    token_env=""
    if [[ "$cli" == "codex" ]]; then
      token_env=$(codex_treg_token_env_var)
    fi
    if [[ -n "$token_env" ]]; then
      if [[ -n "${!token_env:-}" ]]; then
        printf '%s\n' "treg MCP: configured (${token_env} set)"
      else
        printf '%s\n' "treg MCP: configured, but ${token_env} is not set in this environment (Codex cannot authenticate)"
      fi
    else
      printf '%s\n' "treg MCP: configured"
    fi
  else
    printf '%s\n' "treg MCP: not configured"
  fi

  if [[ "$cli" == "grok" ]]; then
    dups=$(duplicate_names || true)
    if [[ -z "$dups" ]]; then
      printf '%s\n' "marketplace duplicate: no"
    else
      printf '%s\n' "marketplace duplicate: yes"
      while IFS= read -r version; do
        [[ -n "$version" ]] || continue
        printf '%s\n' "  ${version}"
      done <<< "$dups"
    fi
  fi

  if [[ "$cli" == "grok" ]] && grok_has_notes_dir; then
    printf '%s\n' "FREE_RESEARCH_NOTES_DIR: set via Grok config"
  elif [[ -n "${FREE_RESEARCH_NOTES_DIR:-}" ]]; then
    printf '%s\n' "FREE_RESEARCH_NOTES_DIR: set"
  else
    printf '%s\n' "FREE_RESEARCH_NOTES_DIR: not set"
  fi
  printf '\n'
}

print_next_steps() {
  local any=0
  local cli config_dir label dups token_env
  printf '%s\n' "Next steps"
  for spec in "claude|.claude|Claude Code" "grok|.grok|Grok" "codex|.codex|Codex" "agy|.gemini|Gemini (agy)"; do
    cli=${spec%%|*}
    spec=${spec#*|}
    config_dir=${spec%%|*}
    label=${spec#*|}
    if ! host_present "$cli" "$config_dir"; then
      printf '%s\n' "- ${label} was not found."
      any=1
      continue
    fi
    if [[ ! -f "$HOME/$config_dir/skills/free-research/SKILL.md" ]]; then
      printf '%s\n' "- Run scripts/install.sh to install the skill for ${label}."
      any=1
    fi
    if ! last30days_present "$HOME/$config_dir"; then
      printf '%s\n' "- Install last30days for ${label}: npx skills add mvanhorn/last30days-skill -g, or copy an existing last30days skill folder into ~/${config_dir}/skills."
      any=1
    fi
    if ! treg_configured "$cli"; then
      printf '%s\n' "- Export TREG_TOKEN and run scripts/install.sh --with-treg for ${label}."
      any=1
    elif [[ "$cli" == "codex" ]]; then
      token_env=$(codex_treg_token_env_var)
      if [[ -n "$token_env" && -z "${!token_env:-}" ]]; then
        printf '%s\n' "- Export ${token_env} in the environment where Codex reads it, then restart Codex."
        any=1
      fi
    fi
    # Grok's own config can set the variable; for other hosts only the environment counts.
    if [[ -z "${FREE_RESEARCH_NOTES_DIR:-}" ]] && { [[ "$cli" != "grok" ]] || ! grok_has_notes_dir; }; then
      printf '%s\n' "- FREE_RESEARCH_NOTES_DIR is not set for ${label}."
      any=1
    fi
  done
  if agents_present; then
    if [[ ! -f "$AGENTS_DIR/free-research/SKILL.md" ]]; then
      printf '%s\n' "- Run scripts/install.sh with the same --agents-dir selection to install the skill for Other agents."
      any=1
    fi
    if [[ ! -d "$AGENTS_DIR/last30days" ]]; then
      printf '%s\n' "- Install last30days for Other agents: npx skills add mvanhorn/last30days-skill -g, or copy an existing last30days skill folder into ${AGENTS_DIR}."
      any=1
    fi
  fi
  dups=$(duplicate_names || true)
  if [[ -n "$dups" ]]; then
    printf '%s\n' "- Grok marketplace duplicate is present (free-research-skill-*). Remove it if you want only the native skill."
    any=1
  fi
  if [[ "$any" -eq 0 ]]; then
    printf '%s\n' "- Nothing else to set up for the hosts found on this Mac."
  fi
}

print_check() {
  print_host_status "Claude Code" claude .claude
  print_host_status "Grok" grok .grok
  print_host_status "Codex" codex .codex
  print_host_status "Gemini (agy)" agy .gemini
  print_agents_status
  print_next_steps
}

agents_present() {
  [[ "$AGENTS_EXPLICIT" -eq 1 || -d "$AGENTS_DIR" ]]
}

print_agents_status() {
  local version
  printf '%s\n' "== Other agents (~/.agents/skills) =="
  if agents_present; then
    printf '%s\n' "host: found (skills directory selected)"
  else
    printf '%s\n' "host: not found"
  fi
  if [[ -f "$AGENTS_DIR/free-research/SKILL.md" ]]; then
    version=$(skill_version "$AGENTS_DIR/free-research/SKILL.md")
    printf '%s\n' "skill: installed ${version:-(version unknown)}"
  else
    printf '%s\n' "skill: not installed"
  fi
  if [[ -d "$AGENTS_DIR/last30days" ]]; then
    printf '%s\n' "last30days: present"
  else
    printf '%s\n' "last30days: missing"
  fi
  printf '%s\n\n' "treg MCP: each agent must have treg MCP configured itself."
}

# Lists every real file and directory under the skill source, one per call.
list_skill_paths() {
  (cd "$SKILL_SRC" && find . \( -name "__pycache__" -o -name ".DS_Store" \) -prune -o -print0)
}

copy_skill() {
  local label="$1"
  local dest_root="$2"
  local rel src_path dest_path src_mtime dest_mtime
  local rels=()
  local newer=()
  local blocked=""

  if [[ ! -d "$SKILL_SRC" ]]; then
    printf '%s\n' "Missing skill source: skills/free-research" >&2
    exit 1
  fi
  if [[ -L "$dest_root" ]]; then
    printf '%s\n' "Refusing to install for ${label}: destination is a symlink (${dest_root}). Nothing was changed." >&2
    SYMLINK_REFUSED=1
    return 0
  fi

  # Preflight every path first so a host is never left half-updated.
  while IFS= read -r -d '' rel; do
    rel="${rel#./}"
    if [[ -z "$rel" || "$rel" == "." ]]; then
      continue
    fi
    src_path="$SKILL_SRC/$rel"
    dest_path="$dest_root/$rel"
    if [[ -L "$src_path" ]]; then
      continue
    fi
    if [[ -d "$src_path" ]]; then
      if [[ -L "$dest_path" ]]; then
        blocked="$rel"
      fi
      continue
    fi
    if [[ ! -f "$src_path" ]]; then
      continue
    fi
    rels[${#rels[@]}]="$rel"
    if [[ -f "$dest_path" && ! -L "$dest_path" && "$FORCE" -eq 0 ]] && ! cmp -s "$src_path" "$dest_path"; then
      src_mtime=$(stat -f %m "$src_path")
      dest_mtime=$(stat -f %m "$dest_path")
      if [[ "$dest_mtime" -gt "$src_mtime" ]]; then
        newer[${#newer[@]}]="$rel"
      fi
    fi
  done < <(list_skill_paths)

  if [[ -n "$blocked" ]]; then
    printf '%s\n' "Refusing to install for ${label}: destination directory is a symlink (${dest_root}/${blocked}). Nothing was changed." >&2
    SYMLINK_REFUSED=1
    return 0
  fi
  if [[ "${#newer[@]}" -gt 0 ]]; then
    for rel in "${newer[@]}"; do
      printf '%s\n' "refusing to overwrite newer file: ${rel}"
    done
    printf '%s\n' "Skipped ${label}: no files were written."
    SKIPPED_ANY=1
    return 0
  fi

  mkdir -p "$dest_root"
  for rel in "${rels[@]}"; do
    src_path="$SKILL_SRC/$rel"
    dest_path="$dest_root/$rel"
    mkdir -p "$(dirname "$dest_path")"
    if [[ -L "$dest_path" ]]; then
      rm -f "$dest_path"
    fi
    cp -p "$src_path" "$dest_path"
  done
  printf '%s\n' "Installed free-research for ${label}."
}

install_skills() {
  if host_present claude .claude; then
    copy_skill "Claude Code" "$HOME/.claude/skills/free-research"
  fi
  if host_present grok .grok; then
    copy_skill "Grok" "$HOME/.grok/skills/free-research"
  fi
  if host_present codex .codex; then
    copy_skill "Codex" "$HOME/.codex/skills/free-research"
  fi
  if host_present agy .gemini; then
    copy_skill "Gemini (agy)" "$HOME/.gemini/skills/free-research"
  fi
  if agents_present; then
    copy_skill "Other agents" "$AGENTS_DIR/free-research"
  fi
}

report_missing() {
  local missing=()
  local count
  if ! host_present claude .claude; then
    missing[${#missing[@]}]="Claude Code"
  fi
  if ! host_present grok .grok; then
    missing[${#missing[@]}]="Grok"
  fi
  if ! host_present codex .codex; then
    missing[${#missing[@]}]="Codex"
  fi
  if ! host_present agy .gemini; then
    missing[${#missing[@]}]="Gemini (agy)"
  fi
  count=${#missing[@]}
  if [[ "$count" -eq 0 ]]; then
    return 0
  fi
  if [[ "$count" -eq 1 ]]; then
    printf '%s\n' "${missing[0]} was not found."
    return 0
  fi
  if [[ "$count" -eq 2 ]]; then
    printf '%s\n' "${missing[0]} and ${missing[1]} were not found."
    return 0
  fi
  if [[ "$count" -eq 3 ]]; then
    printf '%s\n' "${missing[0]}, ${missing[1]}, and ${missing[2]} were not found."
  else
    printf '%s\n' "${missing[0]}, ${missing[1]}, ${missing[2]}, and ${missing[3]} were not found."
  fi
}

# Runs a host CLI, capturing combined output in MCP_OUTPUT and status in MCP_STATUS.
run_mcp_capture() {
  local cli="$1"
  shift
  set +e
  MCP_OUTPUT=$("$cli" "$@" 2>&1)
  MCP_STATUS=$?
  set -e
}

report_mcp_failure() {
  local cli="$1"
  local verb="$2"
  printf '%s\n' "${cli} mcp ${verb} failed." >&2
  printf '%s\n' "$MCP_OUTPUT" | redact >&2
}

run_mcp_add() {
  local cli="$1"
  shift
  run_mcp_capture "$cli" "$@"
  if [[ "$MCP_STATUS" -ne 0 ]]; then
    report_mcp_failure "$cli" add
    return 1
  fi
  return 0
}

# A failed remove is harmless only when the server was not there to remove.
remove_treg_host() {
  local cli="$1"
  case "$cli" in
    claude) run_mcp_capture claude mcp remove treg -s user ;;
    grok) run_mcp_capture grok mcp remove treg ;;
    codex) run_mcp_capture codex mcp remove treg ;;
    agy) run_mcp_capture agy mcp remove treg ;;
    *)
      printf '%s\n' "Unknown host: ${cli}" >&2
      return 1
      ;;
  esac
  if [[ "$MCP_STATUS" -eq 0 ]]; then
    return 0
  fi
  if printf '%s\n' "$MCP_OUTPUT" | grep -Eiq 'not found|does not exist|no such|no mcp server|unknown (mcp )?server|not configured'; then
    return 0
  fi
  report_mcp_failure "$cli" remove
  return 1
}

# Sets HOST_RESULT to a short outcome; returns 1 only when the host failed.
add_treg_host() {
  local cli="$1"
  local label="$2"
  local already=0
  HOST_RESULT=""
  if ! command -v "$cli" >/dev/null 2>&1; then
    printf '%s\n' "${label} CLI was not found. Skipped treg MCP setup."
    HOST_RESULT="skipped (CLI not found)"
    return 0
  fi
  if treg_configured "$cli"; then
    already=1
  fi
  if [[ "$already" -eq 1 && "$FORCE" -eq 0 ]]; then
    printf '%s\n' "${label}: treg MCP already configured."
    HOST_RESULT="already configured"
    return 0
  fi
  if [[ "$already" -eq 1 ]] && ! remove_treg_host "$cli"; then
    HOST_RESULT="FAILED (remove)"
    return 1
  fi
  case "$cli" in
    claude)
      run_mcp_add claude mcp add --scope user --transport http treg "$TREG_URL" -H "Authorization: Bearer ${TREG_TOKEN}" || {
        HOST_RESULT="FAILED (add)"
        return 1
      }
      ;;
    grok)
      run_mcp_add grok mcp add treg "$TREG_URL" -H "Authorization: Bearer ${TREG_TOKEN}" || {
        HOST_RESULT="FAILED (add)"
        return 1
      }
      ;;
    codex)
      run_mcp_add codex mcp add treg --url "$TREG_URL" --bearer-token-env-var TREG_TOKEN || {
        HOST_RESULT="FAILED (add)"
        return 1
      }
      ;;
    agy)
      run_mcp_add agy mcp add -H "Authorization: Bearer ${TREG_TOKEN}" treg "$TREG_URL" || {
        HOST_RESULT="FAILED (add)"
        return 1
      }
      ;;
    *)
      printf '%s\n' "Unknown host: ${cli}" >&2
      HOST_RESULT="FAILED (unknown host)"
      return 1
      ;;
  esac
  if [[ "$already" -eq 1 ]]; then
    HOST_RESULT="replaced"
  else
    HOST_RESULT="added"
  fi
  return 0
}

# Every present host is attempted; one failure never stops the others.
add_treg() {
  local failed=0
  local results=""
  local spec cli config_dir label
  for spec in "claude|.claude|Claude Code" "grok|.grok|Grok" "codex|.codex|Codex" "agy|.gemini|Gemini (agy)"; do
    cli=${spec%%|*}
    spec=${spec#*|}
    config_dir=${spec%%|*}
    label=${spec#*|}
    if ! host_present "$cli" "$config_dir"; then
      continue
    fi
    if ! add_treg_host "$cli" "$label"; then
      failed=1
    fi
    results="${results}${label}: treg MCP ${HOST_RESULT}"$'\n'
  done
  if [[ -n "$results" ]]; then
    printf '%s\n' "treg MCP results"
    printf '%s' "$results"
  fi
  return "$failed"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK=1 ;;
    --with-treg) WITH_TREG=1 ;;
    --force) FORCE=1 ;;
    --agents-dir)
      if [[ $# -lt 2 || -z "$2" || "$2" == -* ]]; then
        printf '%s\n' "--agents-dir requires a path." >&2
        exit 2
      fi
      AGENTS_DIR="$2"
      AGENTS_EXPLICIT=1
      shift
      ;;
    --help | -h)
      usage
      exit 0
      ;;
    *)
      case "$1" in
        -*) printf '%s\n' "Unknown option: $1" | redact >&2 ;;
        *) printf '%s\n' "Unknown argument." >&2 ;;
      esac
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "$CHECK" -eq 1 ]]; then
  print_check | redact
  exit 0
fi

install_skills
TREG_FAILED=0
if [[ "$WITH_TREG" -eq 1 ]]; then
  if [[ -z "${TREG_TOKEN:-}" ]]; then
    printf '%s\n' "TREG_TOKEN is missing. Skipped treg MCP setup."
  elif [[ "$TREG_TOKEN" == *[[:cntrl:]]* ]]; then
    printf '%s\n' "TREG_TOKEN contains control characters or a newline. Skipped treg MCP setup." >&2
    TREG_FAILED=1
  else
    add_treg || TREG_FAILED=1
  fi
fi
report_missing
if [[ "$SKIPPED_ANY" -eq 1 ]]; then
  printf '%s\n' "Newer destination files were kept. Re-run with --force to overwrite."
  exit 1
fi
if [[ "$SYMLINK_REFUSED" -eq 1 || "$TREG_FAILED" -eq 1 ]]; then
  exit 1
fi
exit 0
