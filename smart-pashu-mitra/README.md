# Smart Pashu Mitra

Digital Livestock Assistant for Rural Farmers — built for the DYPIU Rural
Internship Programme (Animal Husbandry Department, Jalgaon Jamod).

## What's included

- Farmer registration
- Animal registration (linked to a farmer)
- Vaccination tracker (flags overdue vaccinations automatically)
- Health Assistant (rule-based advice for common symptoms, logs every query)
- Government schemes page
- Dashboard with live counts

## Tech stack

- Backend: Python Flask
- Database: SQLite (file-based, no server install needed)
- Frontend: HTML, CSS (no framework — a hand-built design system in
  `static/css/style.css`)

## How to run it on your laptop

1. Make sure Python 3.10+ is installed. Check with:
   ```
   python3 --version
   ```

2. Open a terminal in this folder (`smart-pashu-mitra`) and install Flask:
   ```
   pip install -r requirements.txt
   ```
   (If `pip` doesn't work, try `pip3`.)

3. Run the app:
   ```
   python3 app.py
   ```
   The first time you run it, it will automatically create the database
   file at `database/pashu_mitra.db` from `database/schema.sql`.

4. Open your browser and go to:
   ```
   http://127.0.0.1:5000
   ```

5. To stop the server, press `Ctrl+C` in the terminal.

## Folder structure

```
smart-pashu-mitra/
├── app.py                  # Flask app: all routes and logic
├── requirements.txt
├── database/
│   ├── schema.sql           # Table definitions
│   └── pashu_mitra.db       # Created automatically on first run
├── static/
│   └── css/
│       └── style.css        # All styling
└── templates/
    ├── base.html             # Shared layout, nav, flash messages
    ├── index.html             # Home page
    ├── dashboard.html
    ├── farmers.html / add_farmer.html
    ├── animals.html / add_animal.html
    ├── vaccinations.html / add_vaccination.html
    ├── health.html
    └── schemes.html
```

## Starting fresh / resetting data

Delete `database/pashu_mitra.db` and restart the app — it will recreate an
empty database automatically.

## For your internship report / viva

- **Database design**: 4 tables — `farmers`, `animals`, `vaccinations`,
  `health_queries` — with foreign keys linking animals to farmers and
  vaccinations to animals. Screenshot `database/schema.sql` for your ER
  diagram section.
- **Health Assistant** currently uses a rule-based dictionary
  (`HEALTH_RULES` in `app.py`) rather than real AI — this matches what was
  scoped for your internship timeline. It's called out as a "Future Scope"
  item if you want to add a real chatbot (e.g. Gemini API) later.
- **To demo overdue vaccination logic**: add a vaccination with a due date
  in the past — it will automatically show a red "Overdue" tag on the
  Vaccinations page and count toward "Vaccinations Due" on the dashboard.

## Next steps you could add later (Future Scope)

- SMS/WhatsApp vaccination reminders
- A real AI chatbot for the Health Assistant (Gemini/OpenAI API)
- Marathi language support
- Edit functionality for farmer/animal/vaccination records (currently
  add + view + delete only, which is enough for the MVP)
