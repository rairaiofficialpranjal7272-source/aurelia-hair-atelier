# Aurelia Hair Atelier — website concept

A responsive, editorial-style salon website with a working appointment booking flow and a small salon admin dashboard. This repository preserves the existing HTML/CSS/JavaScript design and its five local image assets.

> This is a concept/demo. Salon address, contact details, staff, and prices remain placeholders. Update those before using it for a real salon.

## Project contents

- `index.html` — customer-facing website, responsive styling and interactions, booking form.
- `admin.html` — password-key protected booking/service management dashboard.
- `server.py` — Python standard-library HTTP server and JSON API, validation, SQLite persistence.
- `assets/` — local images used by the site.
- `render.yaml` — optional Render deployment blueprint, with persistent disk and generated admin key.

There is no JavaScript framework or npm dependency. Python 3.9+ is required to run the backend. All API and database behavior uses Python's standard library and SQLite.

## Run locally

From the project root:

```bash
python3 server.py
```

Open <http://localhost:4173>. The dashboard is at <http://localhost:4173/admin>. Local demo admin key: `change-me`.

For local testing with your own admin password:

```bash
ADMIN_KEY='choose-a-long-random-secret' python3 server.py
```

The app creates `aurelia.sqlite3` locally on first launch. Booking records are deliberately excluded from Git. To use a different persistent database location, set `DB_PATH`.

## Booking behavior

- Service options load from the server's services table. Added services in the dashboard become available in the form immediately.
- Date and time availability is returned by the backend and checked again atomically when a booking is submitted.
- Server-side validation covers name, international phone format, email, active service, future date, Sunday closure, time slot, and note length.
- SQLite saves bookings and their status. The admin dashboard can view bookings, change status, and add/remove services.
- Booking time slots are configured in `server.py` (`SLOTS`). Sunday is closed; adjust `valid_date()` if the salon schedule differs.

## Important security and operational notes

- **Never use the default `change-me` key on a public deployment.** Set a unique secret as the `ADMIN_KEY` environment variable. Do not commit `.env` files or secrets.
- The current admin API uses a shared key, not user accounts, role management, or rate limiting. Add proper authentication and HTTPS/security hardening before production use.
- SQLite is suitable for a small single-service deployment. Use a persistent disk/volume for the database. Without one, many hosting platforms erase local data on restart/redeploy. For multi-instance/high-volume production, move to managed PostgreSQL and add backups.
- This demo does not send email/SMS confirmations, integrate a payment provider, or sync with a calendar. The on-screen confirmation is not a notification to the salon/customer.
- Ensure image licensing/permissions are appropriate before commercial use.

## Hosting and GitHub Pages

GitHub Pages can serve the static HTML and images, but **cannot run `server.py`, SQLite, the service admin panel, or save bookings**. Deploy the complete functioning site to a Python-capable host with persistent storage, or separately build/host an API and update the frontend API URLs/CORS configuration. The included `render.yaml` is an example Render service configured with a persistent disk and generated `ADMIN_KEY`; confirm current platform pricing and settings before deploying.

## Deploy using Render (recommended simple full-stack path)

1. Push this repository to GitHub (steps below).
2. In Render, choose **New → Blueprint**, connect the repository, and apply `render.yaml`.
3. Confirm the web service and persistent disk settings. The Blueprint generates `ADMIN_KEY`; do not replace it with `change-me`.
4. After deployment, open the provided service URL. Append `/admin` for the dashboard.
5. Review the service logs and create a test booking. Confirm the record appears in the admin dashboard.

If you change database hosting, configure `DB_PATH` to a path on the persistent volume, e.g. `/var/data/aurelia.sqlite3`.

## Upload to a new GitHub repository

A prepared ZIP can be used if GitHub access is not connected. Extract its top-level `aurelia-hair-atelier` folder, then:

```bash
cd path/to/aurelia-hair-atelier
git init
git add .
git commit -m "Prepare Aurelia Hair Atelier website"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/aurelia-hair-atelier.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username. First create an **empty** repository named `aurelia-hair-atelier` on GitHub; leave README/license initialization unchecked so it doesn't conflict with this project. If your GitHub repository URL differs, use that exact URL instead.

If `git remote add origin` says the remote already exists, inspect it first with `git remote -v`; do not overwrite an existing repository/history without checking. If Git says `src refspec main does not match any`, ensure `git add .` and `git commit` succeeded. For HTTPS authentication, use Git Credential Manager or GitHub CLI (`gh auth login`); GitHub account passwords are not accepted as Git passwords. Never paste tokens into source files or commit them.
