#!/bin/bash
# review-watch.sh REPO...: print one REVIEW line when the unreviewed
# range on $BRANCH (default: the current branch of each repo) crosses
# the threshold, then mark it as handed out. REVIEW_SKIP lists the
# path patterns that do not count (default: *.md *.org).
REVIEW_SKIP=${REVIEW_SKIP:-*.md *.org}
set -f; skip=(); for p in $REVIEW_SKIP; do skip+=(":!$p"); done; set +f
REVIEW_LINES=${REVIEW_LINES:-100} REVIEW_COMMITS=${REVIEW_COMMITS:-5} EVERY=${EVERY:-300}
STATE=${STATE:-$HOME/.cache/review-watch}; mkdir -p "$STATE"
declare -A skipped
while true; do
  for r in "$@"; do
    b=${BRANCH:-$(git -C "$r" branch --show-current)}
    if [ -z "$b" ]; then
      [ -n "${skipped[$r]}" ] || echo "SKIP $r: detached HEAD"
      skipped[$r]=1; continue
    fi
    unset "skipped[$r]"
    f=$STATE/$(realpath "$r" | tr / _)
    head=$(git -C "$r" rev-parse -q --verify "$b") || continue
    [ -s "$f" ] || { echo "$head" > "$f"; continue; }
    last=$(cat "$f")
    [ "$head" = "$last" ] && continue
    # stored commit gone (rewritten history, gc): restart from the current head
    git -C "$r" merge-base --is-ancestor "$last" "$head" 2>/dev/null ||
      last=$(git -C "$r" merge-base "$last" "$head" 2>/dev/null) ||
      { echo "$head" > "$f"; continue; }
    n=$(git -C "$r" rev-list --count "$last..$head" -- . "${skip[@]}")
    code=$(git -C "$r" diff --numstat "$last" "$head" -- . "${skip[@]}" | awk '{s+=$1+$2} END {print s+0}')
    if [ "$code" -ge "$REVIEW_LINES" ] || [ "$n" -ge "$REVIEW_COMMITS" ]; then
      echo "REVIEW $r ${last:0:7}..${head:0:7} commits=$n code_lines=$code"
      echo "$head" > "$f"
    fi
  done
  sleep "$EVERY"
done
