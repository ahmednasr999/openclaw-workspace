# OAuth Pattern: Account Ownership Conflict

## The Problem
When authenticating Google OAuth:
- Same Google account = project owner + user = BLOCKED
- Different accounts = works

## The Solution
- Project owner: `nasr.ai.assistant@gmail.com`
- Authenticated user: `ahmednasr999@gmail.com`
- Different accounts = no conflict = WORKS

## Root Cause
Google blocks adding yourself as a test user to your own project. This is a security restriction.

## Lesson
When OAuth blocks the project owner account:
1. Use a DIFFERENT account to own the project
2. Then authenticate the target user
3. Never try to auth the same account that owns the project
