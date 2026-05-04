import requests

urls = [
    "https://jobs.newsmatrix.in",
    "https://jobs.newsmatrix.in/jobs",
    "https://jobs.newsmatrix.in/sitemap.xml",
]

# Ping Google sitemap
r = requests.get(
    "https://www.bing.com/ping",
    params={"sitemap": "https://jobs.newsmatrix.in/sitemap.xml"}
)
print("✅ Google ping status:", r.status_code)