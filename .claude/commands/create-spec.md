---
description: Create specification file and feature branch for new feature
argument-hint: "Step number and feature name e.g 1 registration"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

you are a technical project manager responsible for spinning new features for expense traker.
Always follow CLAUDE.md rules

User input: $ARGUMENTS

## Step 1 - Check working directory is clean

Run `git status` and check for uncommitted, unstaged, or
untracked files. If any exist, stop immediately and tell
the user with message starting with "👀" to commit or stash changes before proceeding.
DO NOT CONTINUE until the working directory is clean.

## Step 2 - Parse the Arguments

from $ARGUMENTS extracts:

1. `step_number` — zero-padded to 2 digits: 2 → 02, 11 → 11

2. `feature_title` — human readable title in Title Case
   - Example: "Registration" or "Login and Logout"

3. `feature_slug` — git and file safe slug
   - Lowercase, kebab-case
   - Only a-z, 0-9 and -
   - Maximum 40 characters
   - Example: registration, login-logout

4. `branch_name` — format: `feature/<feature_slug>`
   - Example: `feature/registration`

If you cannot infer these from $ARGUMENTS, ask the user
to clarify before proceeding.

## Step 3 - Check branch name is not taken

Run `git branch` and chekc branch name.
If `branch_name` is taken, append a number with it e.g `branch_name-01`

## Step 4 - Research the codebase

Read and analyse entire code base before attempting to made any change in codebase.
Check `CLAUDE.md` to confirm that requested feature is not already marked complete.If available mark the user and STOP.

## Step 5 - Write a specification file

Generate a spec file as per below instructions

# Spec: <Feature_title>

## Overview:

One paragaraph overview on what does this feature do and its role in verflow application

## Dependencies

Ecxplain any feature dependencies if any
Else say "No feature dependency"

## Navigation approach (Route or link)

Describe every new route needed for features with end to end navigation approaches
If no route state "No new routes needed"

## Existing Files changes

Description of every application file needed change with small reason (2 to 3 sentences)

If no file chnge needed say "No chnage require in existing file"

## New Files

Explain all the new files needed for this feature with short (2 to 3 sentences) proper reasoning

## Any Packages dependencies

Any new packages needed if not say "No packages dependencies "

## Constraint Rules

Specific constraints model must follow:

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Defenation of done:

A specific testable checklist. Each items must be verified while running application

## Save spec file

Save to : `.claude/specs/<step_number>-<feature_slug>.md`

## Updated when done

Print a short summary in below format:

- Feature : <branch_name>
- Spec file: .claude/specs/<step_number>-<feature_slug>.md
- Title: <feature_title>

Aske user to review the spec file with file location link
You can use plan mode with Shift + Tab twice to begin implementation

Never print full spec in chat terminal unless asked
