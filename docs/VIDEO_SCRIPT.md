# Video script

A walkthrough of the deployed application, roughly 4–5 minutes. Screen recording with a
voice-over or subtitles; the order below matches the tester's checklist.

Preparation: seed 30+ top level comments so the pagination is visible, one thread three
levels deep, one comment with an image and one with a TXT file. Two browser windows side by
side — the second one is needed for the real time part.

---

## 1. First look (0:00–0:30)

- Open the site at its public address.
- Show the table: user name, e-mail, date, message excerpt, number of replies.
- Say out loud: 25 comments per page, newest first.
- Open the browser console for a second — no errors.

## 2. Sorting and pagination (0:30–1:00)

- Click "User Name" — sorted ascending; click again — descending, the arrow flips.
- Do the same for "E-mail" and "Date".
- Go to page 2 and back.

## 3. The thread (1:00–1:30)

- Expand a row: the top level comment and its replies with indentation.
- Show a reply to a reply and a third level one — the depth is unlimited.
- Point at the avatar with initials, the date and the author name that links to their home
  page.

## 4. Writing a comment (1:30–2:30)

- Press **Send** with an empty form: every required field shows its own error.
- Type a cyrillic name — "Only latin letters and digits are allowed"; fix it.
- Type an invalid e-mail — the error appears; fix it.
- In the message, select a word and press `[strong]`, then `[i]` — the tags wrap the
  selection.
- Type `<b>bold</b>` — the error names the tag; remove it.
- Press **Preview** — the formatted message is rendered without a page reload.
- Enter a wrong CAPTCHA — the error appears **and a new image is loaded**.
- Enter the correct code and send — the comment appears at the top of the table.

## 5. Attachments (2:30–3:15)

- Attach a large photo (for example 1920×1080) and send.
- Open the thread: the image is already resized to 320×240.
- Click it — a modal window with animation over a dimmed page.
- Close it with Esc, open again and close by clicking the backdrop.
- Open the comment with a TXT file — the contents are shown in the same modal.
- Try to attach a `.bmp` file — the error appears before anything is sent.

## 6. Replies and real time (3:15–4:00)

- Put the two windows side by side.
- In the left one, answer a comment inside an open thread.
- In the right one — **without a reload** — the reply shows up in the thread and the replies
  counter grows.
- Add a top level comment in the left window: in the right one it appears at the top of the
  table.
- Mention the indicator in the header: "live" means the WebSocket connection is open.

## 7. Accounts (4:00–4:40)

- "Sign in" → "Register" → create an account.
- The header shows "Signed in as …"; in the form the name and e-mail are filled in from the
  account and disabled.
- Send a comment — it is signed with the account name.
- "Log out" — the fields are empty and editable again.
- Reload the page while signed in — the session is restored.

## 8. Under the hood (4:40–5:00)

- Open `/admin/` and show the comment list with filters and search.
- Optional: `docker compose logs worker` with the notification e-mail that was queued for
  the parent comment's author.
- Optional: `docker compose ps` — five services: db, redis, backend, worker, nginx.

---

## What is worth saying explicitly

- The message is not simply escaped: the server validates the tags and rebuilds the HTML,
  and exactly that string is stored.
- Sorting accepts only whitelisted fields; anything else falls back to the default.
- New comments arrive over WebSocket, so no tab polls the server.
- The notification to the parent author is handled by a queue, so it never slows the form
  down.
