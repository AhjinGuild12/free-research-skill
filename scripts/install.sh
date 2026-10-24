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
SKIPPED_ANY=0

usage() {
  cat <<'EOF'
Usage: scripts/install.sh [--check] [--with-treg] [--force] [--help]

Copy skills/free-research into each present host's skills directory.
A host is present when its CLI is on PATH or its config directory exists
(~/.claude, ~/.grok, or ~/.codex). The copy is real files, not a symlink.
__pycache__ and .DS_Store are skipped. A destination file newer than the
repo file is left in place unless --force.

Options:
  --check       Print one status block per host and a next-steps list.
                Does not copy files or add MCP servers. Always exits 0.
  --with-treg   Add the treg MCP server (https://treg.to/mcp/) for each
                present host. Requires TREG_TOKEN in the environment.
                Skips a host that already has treg configured unless --force.
                The token is not printed, logged, or written into the repo.
  --force       Overwrite newer destination files and re-add treg MCP.
  --help        Show this help.

Exit status:
  0  install finished, --check, or --help
  1  a newer destination file was kept, or a treg MCP command failed
  2  unknown option
EOF
}

redact() {
  awk '
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
    }
    {
      line = $0
      line = replace_all(line, token, "***")
      line = replace_all(line, notes, "***")
      prefix = "Authorization: Bearer "
      i = index(line, prefix)
      if (i > 0) {
        head = substr(line, 1, i + length(prefix) - 1)
        tail = substr(line, i + length(prefix))
        n = length(tail)
        for (j = 1; j <= length(tail); j++) {
          c = substr(tail, j, 1)
          if (c == " " || c == "\"" || c == "\047" || c == ",") {
            n = j - 1
            break
          }
        }
        line = head "***" substr(tail, n + 1)
      }
      print line
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

json_has_treg_key() {
  awk '
    BEGIN { found = 0 }
    /"treg"[[:space:]]*:/ { found = 1; exit 0 }
    END { exit found ? 0 : 1 }
  ' "$1"
}

toml_has_treg() {
  awk '
    BEGIN { found = 0 }
    /^\[mcp_servers\.treg(\.|])/ { found = 1; exit 0 }
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

grok_has_notes_dir() {
  local file="$HOME/.grok/config.toml"
  [[ -f "$file" ]] || return 1
  awk '
    BEGIN { found = 0 }
    /^[[:space:]]*(FREE_RESEARCH_NOTES_DIR|"FREE_RESEARCH_NOTES_DIR"|\047FREE_RESEARCH_NOTES_DIR\047)[[:space:]]*=/ {
      found = 1
      exit
    }
    END { exit found ? 0 : 1 }
  ' "$file"
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
  esac
  return 1
}

treg_configured() {
  local cli="$1"
  local out
  if config_has_treg "$cli"; then
    return 0
  fi
  if ! command -v "$cli" >/dev/null 2>&1; then
    return 1
  fi
  set +e
  out=$("$cli" mcp list 2>&1)
  set -e
  if text_names_treg "$out"; then
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
  for spec in "claude|.claude|Claude Code" "grok|.grok|Grok" "codex|.codex|Codex"; do
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
      printf '%s\n' "- Install last30days for ${label} (skills directory or plugin cache)."
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
  done
  dups=$(duplicate_names || true)
  if [[ -n "$dups" ]]; then
    printf '%s\n' "- Grok marketplace duplicate is present (free-research-skill-*). Remove it if you want only the native skill."
    any=1
  fi
  if [[ -z "${FREE_RESEARCH_NOTES_DIR:-}" ]] && ! grok_has_notes_dir; then
    printf '%s\n' "- FREE_RESEARCH_NOTES_DIR is not set."
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
  print_next_steps
}

copy_skill() {
  local label="$1"
  local dest_root="$2"
  local rel src_path dest_path src_mtime dest_mtime

  if [[ ! -d "$SKILL_SRC" ]]; then
    printf '%s\n' "Missing skill source: skills/free-research" >&2
    exit 1
  fi
  mkdir -p "$dest_root"

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
      mkdir -p "$dest_path"
      continue
    fi
    if [[ ! -f "$src_path" ]]; then
      continue
    fi
    mkdir -p "$(dirname "$dest_path")"
    if [[ -L "$dest_path" ]]; then
      rm -f "$dest_path"
    elif [[ -f "$dest_path" && "$FORCE" -eq 0 ]]; then
      src_mtime=$(stat -f %m "$src_path")
      dest_mtime=$(stat -f %m "$dest_path")
      if [[ "$dest_mtime" -gt "$src_mtime" ]]; then
        printf '%s\n' "refusing to overwrite newer file: ${rel}"
        SKIPPED_ANY=1
        continue
      fi
    fi
    cp "$src_path" "$dest_path"
  done < <(
    cd "$SKILL_SRC" && find . \( -name "__pycache__" -o -name ".DS_Store" \) -prune -o -print0
  )
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
  printf '%s\n' "${missing[0]}, ${missing[1]}, and ${missing[2]} were not found."
}

run_mcp_add() {
  local cli="$1"
  shift
  local output status
  set +e
  output=$("$cli" "$@" 2>&1)
  status=$?
  set -e
  if [[ "$status" -ne 0 ]]; then
    printf '%s\n' "${cli} mcp add failed." >&2
    printf '%s\n' "$output" | redact >&2
    return 1
  fi
  return 0
}

add_treg_host() {
  local cli="$1"
  local label="$2"
  if ! command -v "$cli" >/dev/null 2>&1; then
    printf '%s\n' "${label} CLI was not found. Skipped treg MCP setup."
    return 0
  fi
  if [[ "$FORCE" -eq 0 ]] && treg_configured "$cli"; then
    printf '%s\n' "${label}: treg MCP already configured."
    return 0
  fi
  case "$cli" in
    claude)
      run_mcp_add claude mcp add --scope user --transport http treg "$TREG_URL" -H "Authorization: Bearer ${TREG_TOKEN}"
      ;;
    grok)
      run_mcp_add grok mcp add treg "$TREG_URL" -H "Authorization: Bearer ${TREG_TOKEN}"
      ;;
    codex)
      run_mcp_add codex mcp add treg --url "$TREG_URL" --bearer-token-env-var TREG_TOKEN
      ;;
    *)
      printf '%s\n' "Unknown host: ${cli}" >&2
      return 1
      ;;
  esac
}

add_treg() {
  local failed=0
  if host_present claude .claude; then
    add_treg_host claude "Claude Code" || failed=1
  fi
  if host_present grok .grok; then
    add_treg_host grok "Grok" || failed=1
  fi
  if host_present codex .codex; then
    add_treg_host codex "Codex" || failed=1
  fi
  return "$failed"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK=1 ;;
    --with-treg) WITH_TREG=1 ;;
    --force) FORCE=1 ;;
    --help | -h)
      usage
      exit 0
      ;;
    *)
      printf '%s\n' "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "$CHECK" -eq 1 ]]; then
  print_check
  exit 0
fi

install_skills
TREG_FAILED=0
if [[ "$WITH_TREG" -eq 1 ]]; then
  if [[ -z "${TREG_TOKEN:-}" ]]; then
    printf '%s\n' "TREG_TOKEN is missing. Skipped treg MCP setup."
  else
    add_treg || TREG_FAILED=1
  fi
fi
report_missing
if [[ "$SKIPPED_ANY" -eq 1 ]]; then
  printf '%s\n' "Newer destination files were kept. Re-run with --force to overwrite."
  exit 1
fi
if [[ "$TREG_FAILED" -eq 1 ]]; then
  exit 1
fi
exit 0
