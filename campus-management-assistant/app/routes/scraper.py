from flask import Blueprint, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required
from . import require_role
from ..services.scraper_service import add_website, list_websites, scrape_website, scrape_all, list_logs, get_website

scraper_bp = Blueprint('scraper', __name__)


@scraper_bp.get('/admin/scraper')
@login_required
@require_role('admin')
def scraper_home():
    websites = list_websites()
    logs = list_logs(50)
    return render_template('admin/scraper.html', websites=websites, logs=logs)


@scraper_bp.post('/admin/scraper/add')
@login_required
@require_role('admin')
def scraper_add():
    url = request.form.get('url', '').strip()
    if not url:
        flash('Please provide a website URL.', 'error')
        return redirect(url_for('scraper.scraper_home'))

    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'https://' + url

    ok, msg = add_website(url)
    if ok:
        flash('Website added. Use Run or Run All to scrape.', 'success')
    else:
        if msg == 'URL already added':
            flash('Website already exists. Use Run to scrape.', 'info')
        else:
            flash(f'Failed to add website: {msg}', 'error')

    return redirect(url_for('scraper.scraper_home'))


@scraper_bp.post('/admin/scraper/run/<int:website_id>')
@login_required
@require_role('admin')
def scraper_run(website_id: int):
    site = get_website(website_id)
    if site:
        scrape_website(site)
    return redirect(url_for('scraper.scraper_home'))


@scraper_bp.post('/admin/scraper/run-all')
@login_required
@require_role('admin')
def scraper_run_all():
    scrape_all()
    return redirect(url_for('scraper.scraper_home'))
