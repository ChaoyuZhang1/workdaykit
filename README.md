# WorkdayKit — Business days calculator

Static site that counts **business days** between dates (or adds/subtracts business days)
for 95 countries, excluding weekends and public holidays, including China's 调休/补班 rules.

## Features

- Homepage calculator: **days between dates** and **add/subtract business days**
- Country pages: business days per year, monthly breakdown, holiday list
- Free JSON API: `/api/v1/business/{CC}/{YYYY}.json`
- Cross-linked with [HolidayKit](https://holidaykit.pages.dev)

## Data

Built from the HolidayKit dataset (`../holiday-kit/data`):
Nager.Date + OpenHolidays + python-holidays + chinese-days.

## Build

```bash
python build.py
python build.py --site-url https://workdaykit.pages.dev
```

Output: `dist/` — deploy to Cloudflare Pages:

```bash
npx wrangler pages deploy dist --project-name workdaykit --branch main
```

## Deployments

- Production: https://workdaykit.pages.dev
- Related: https://holidaykit.pages.dev
