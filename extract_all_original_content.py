import urllib.request
import urllib.parse
import ssl
import os
import json
import re
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

BASE_URL = 'https://www.wooinhome.com.tw'
IMG_DIR = os.path.join('static', 'images', 'original')
os.makedirs(IMG_DIR, exist_ok=True)

def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def download_image(img_url):
    if not img_url:
        return None
    full_url = urllib.parse.urljoin(BASE_URL, img_url)
    filename = os.path.basename(urllib.parse.urlparse(full_url).path)
    if not filename:
        return None
    local_path = os.path.join(IMG_DIR, filename)
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return f"/static/images/original/{filename}"
    
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = resp.read()
            with open(local_path, 'wb') as f:
                f.write(data)
            print(f"Downloaded image: {filename} ({len(data)} bytes)")
            return f"/static/images/original/{filename}"
    except Exception as e:
        print(f"Failed to download image {full_url}: {e}")
        return None

def main():
    print("=== STARTING COMPLETE SCRAPING OF WOOINHOME.COM.TW ===")
    
    # 1. Fetch Sitemap
    sitemap_xml = fetch_url(f"{BASE_URL}/sitemap.xml")
    urls = []
    if sitemap_xml:
        soup = BeautifulSoup(sitemap_xml, 'html.parser')
        urls = [loc.text.strip() for loc in soup.find_all('loc')]
    
    print(f"Found {len(urls)} URLs in sitemap.")

    data = {
        'about': {},
        'banner_images': [],
        'cases': [],
        'articles': [],
        'faqs': [],
        'seo_guides': []
    }

    # 2. Extract Homepage & Banner Images
    home_html = fetch_url(BASE_URL)
    if home_html:
        home_soup = BeautifulSoup(home_html, 'html.parser')
        for img in home_soup.find_all('img'):
            src = img.get('src')
            if src and ('banner' in src or 'webfile' in src or 'upload' in src or 'logo' in src):
                local_img = download_image(src)
                if local_img and local_img not in data['banner_images']:
                    data['banner_images'].append(local_img)

    # 3. Extract About
    about_html = fetch_url(f"{BASE_URL}/about")
    if about_html:
        about_soup = BeautifulSoup(about_html, 'html.parser')
        main_div = about_soup.find('main') or about_soup.body
        # Find paragraphs
        paragraphs = [p.get_text(strip=True) for p in main_div.find_all(['p', 'h1', 'h2', 'h3']) if p.get_text(strip=True)]
        for img in main_div.find_all('img'):
            src = img.get('src')
            download_image(src)
        data['about'] = {
            'text': "\n\n".join(paragraphs),
            'html': str(main_div)
        }
        print(f"Extracted About page ({len(paragraphs)} paragraphs)")

    # 4. Extract Works (Case Studies)
    work_detail_urls = [u for u in urls if '/works/detail/' in u]
    for w_url in work_detail_urls:
        slug = w_url.split('/')[-1]
        w_html = fetch_url(w_url)
        if not w_html:
            continue
        w_soup = BeautifulSoup(w_html, 'html.parser')
        title = w_soup.title.string.split('|')[0].strip() if w_soup.title else slug
        h1 = w_soup.find('h1')
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
        
        # Download images on page
        case_imgs = []
        for img in w_soup.find_all('img'):
            src = img.get('src')
            if src and ('webfile' in src or 'upload' in src or 'works' in src):
                loc = download_image(src)
                if loc:
                    case_imgs.append(loc)

        text = w_soup.get_text()
        data['cases'].append({
            'slug': slug,
            'url': w_url,
            'title': title,
            'images': case_imgs,
            'text': text[:500]
        })
        print(f"Extracted Case: {title} ({len(case_imgs)} images)")

    # 5. Extract Blog Articles
    blog_detail_urls = [u for u in urls if '/blog/detail/' in u]
    for b_url in blog_detail_urls:
        slug = b_url.split('/')[-1]
        b_html = fetch_url(b_url)
        if not b_html:
            continue
        b_soup = BeautifulSoup(b_html, 'html.parser')
        
        # Extract title
        title = b_soup.title.string.split('|')[0].strip() if b_soup.title else slug
        h1 = b_soup.find('h1')
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)

        # Extract images
        art_imgs = []
        for img in b_soup.find_all('img'):
            src = img.get('src')
            if src and ('webfile' in src or 'upload' in src or 'blog' in src):
                loc = download_image(src)
                if loc:
                    art_imgs.append(loc)

        # Extract content
        content_div = b_soup.find('div', class_=lambda c: c and ('content' in c or 'detail' in c or 'article' in c)) or b_soup.find('article') or b_soup.body
        paragraphs = [p.get_text(strip=True) for p in b_soup.find_all(['p', 'h2', 'h3']) if p.get_text(strip=True) and len(p.get_text(strip=True)) > 15]

        # Date & Author
        date_match = re.search(r'20\d{2}[-/]\d{1,2}[-/]\d{1,2}', b_soup.get_text())
        date_pub = date_match.group(0) if date_match else '2026-03-01'

        data['articles'].append({
            'slug': slug,
            'url': b_url,
            'title': title,
            'date': date_pub,
            'images': art_imgs,
            'summary': paragraphs[0] if paragraphs else title,
            'content': "<br><br>".join([f"<p>{p}</p>" for p in paragraphs[:8]])
        })
        print(f"Extracted Article: {title} ({len(paragraphs)} paragraphs, {len(art_imgs)} images)")

    # 6. Extract FAQ / Questions
    q_html = fetch_url(f"{BASE_URL}/question")
    if q_html:
        q_soup = BeautifulSoup(q_html, 'html.parser')
        # find q & a elements
        q_items = q_soup.find_all(['div', 'li'], class_=lambda c: c and 'item' in c)
        print(f"Found {len(q_items)} FAQ item divs")
        for item in q_items:
            q_text = item.get_text(strip=True)
            if q_text:
                data['faqs'].append(q_text)

    # 7. Extract SEO Guides
    seo_urls = [u for u in urls if '/seo/' in u]
    for s_url in seo_urls:
        slug = s_url.split('/')[-1]
        s_html = fetch_url(s_url)
        if not s_html:
            continue
        s_soup = BeautifulSoup(s_html, 'html.parser')
        title = s_soup.title.string.split('|')[0].strip() if s_soup.title else slug
        h1 = s_soup.find('h1')
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
        paragraphs = [p.get_text(strip=True) for p in s_soup.find_all(['p', 'h2', 'h3']) if p.get_text(strip=True) and len(p.get_text(strip=True)) > 20]
        data['seo_guides'].append({
            'slug': slug,
            'title': title,
            'url': s_url,
            'paragraphs': paragraphs
        })
        print(f"Extracted SEO Guide: {title} ({len(paragraphs)} paragraphs)")

    # Save to data/wooinhome_crawled_data.json
    out_file = os.path.join('data', 'wooinhome_crawled_data.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n=== EXTRACTION FINISHED ===")
    print(f"Articles extracted: {len(data['articles'])}")
    print(f"Cases extracted: {len(data['cases'])}")
    print(f"SEO Guides extracted: {len(data['seo_guides'])}")
    print(f"Banner images: {len(data['banner_images'])}")
    print(f"Saved complete dump to: {out_file}")

if __name__ == '__main__':
    main()
