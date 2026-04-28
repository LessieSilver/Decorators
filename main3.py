import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os



def logger(path):
    def __logger(old_function):
        def new_function(*args, **kwargs):
            result = old_function(*args, **kwargs)

            log_entry = (
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                f"Функция: {old_function.__name__} | "
                f"args: {args} | kwargs: {kwargs} | "
            )

            if isinstance(result, list):
                log_entry += f"Найдено статей: {len(result)}\n"
            else:
                log_entry += f"Результат: {result}\n"

            with open(path, 'a', encoding='utf-8') as f:
                f.write(log_entry)

            return result

        return new_function

    return __logger



KEYWORDS = ['дизайн', 'фото', 'web', 'python']


@logger('parser.log')
def parse_habr_articles(url, keywords):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Ошибка при загрузке страницы: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []

    article_containers = soup.find_all('article')
    if not article_containers:
        article_containers = soup.find_all(class_=re.compile(r'article|post|tm-article', re.I))

    for container in article_containers:
        title_elem = container.find('a', class_=re.compile(r'title|link', re.I))
        if not title_elem:
            title_elem = container.find('a', href=re.compile(r'/ru/articles/\d+'))
        if not title_elem:
            continue

        title = title_elem.get_text(strip=True)
        link = title_elem.get('href')
        if link and not link.startswith('http'):
            link = 'https://habr.com' + link

        date_elem = container.find('time')
        if date_elem:
            date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
        else:
            time_elem = container.find(class_=re.compile(r'time|date|published', re.I))
            date_text = time_elem.get_text(strip=True) if time_elem else ''

        preview_parts = []

        summary = container.find(class_=re.compile(r'summary|body|text|preview', re.I))
        if summary:
            preview_parts.append(summary.get_text(strip=True))

        tags = container.find_all(class_=re.compile(r'tag|hub', re.I))
        for tag in tags:
            preview_parts.append(tag.get_text(strip=True))

        meta = container.find_all(class_=re.compile(r'meta|reading|views', re.I))
        for m in meta:
            preview_parts.append(m.get_text(strip=True))

        preview_text = ' '.join(preview_parts).lower()
        title_lower = title.lower()

        if any(kw.lower() in preview_text or kw.lower() in title_lower for kw in keywords):
            if date_text and 'T' in date_text:
                try:
                    dt = datetime.fromisoformat(date_text.replace('Z', '+00:00'))
                    date_formatted = dt.strftime('%d.%m.%Y %H:%M')
                except:
                    date_formatted = date_text
            else:
                date_formatted = date_text or 'не указано'

            articles.append({
                'date': date_formatted,
                'title': title,
                'link': link
            })

    return articles


def main():
    url = 'https://habr.com/ru/articles/'

    if os.path.exists('parser.log'):
        os.remove('parser.log')

    print(f"Поиск статей с ключевыми словами: {', '.join(KEYWORDS)}\n")

    matching_articles = parse_habr_articles(url, KEYWORDS)

    if matching_articles:
        print(f"Найдено {len(matching_articles)} подходящих статей:\n")
        for article in matching_articles:
            print(f"{article['date']} – {article['title']} – {article['link']}")
    else:
        print("Статьи, содержащие ключевые слова, не найдены")

    print(f"\nЛог сохранён в файле 'parser.log'")


if __name__ == '__main__':
    main()