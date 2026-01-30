# DRAFT

Set visibility to public.

Use the same workflow as before, with `VISIBILITY="public"`.

## Prereqs

```bash
gh auth login
```

## Config

```bash
SOURCE_OWNER="wavefnx"
TARGET_OWNER="YOUR_GITHUB_USERNAME_OR_ORG"
VISIBILITY="public"
LIMIT=1000
```

## Mirror all repos (code + full git history)

```bash
mkdir -p /tmp/gh-mirror && cd /tmp/gh-mirror

gh repo list "$SOURCE_OWNER" --limit "$LIMIT" --json name,isArchived,isFork \
  | jq -r '.[] | select(.isArchived==false) | .name' \
  | while read -r REPO; do
      SRC="${SOURCE_OWNER}/${REPO}"
      DST="${TARGET_OWNER}/${REPO}"

      echo "==> Mirroring $SRC -> $DST"

      rm -rf "${REPO}.git"
      git clone --mirror "https://github.com/${SRC}.git" "${REPO}.git"
      cd "${REPO}.git"

      gh repo view "$DST" >/dev/null 2>&1 || gh repo create "$DST" --public --confirm

      git remote set-url origin "https://github.com/${DST}.git"
      git push --mirror

      cd ..
    done
```

Optional: skip forks too. Replace the `jq` line with:

```bash
jq -r '.[] | select(.isFork==false) | select(.isArchived==false) | .name'
```

## Acceptance test

Pick one repo and confirm branches and tags exist on the new public repo:

```bash
git ls-remote https://github.com/$TARGET_OWNER/<repo>.git
```

Confirm it matches the source.

## Follow-ups

1. Next action: set `TARGET_OWNER` to your GitHub username/org and run the script.
2. Edge case: if any repo uses Git LFS, you’ll need `git lfs fetch --all` then `git lfs push --all origin` per repo.
3. Failure mode: name collisions or missing token scopes will break `gh repo create`/`git push`; prefix repo names or re-auth with appropriate scopes.

## Stop rule

Stop once one randomly sampled repo has matching commits/tags and the target owner shows the expected repo count.
