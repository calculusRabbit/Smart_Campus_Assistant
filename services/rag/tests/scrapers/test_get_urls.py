from scrapers.get_urls import filter_urls


def test_drops_urls_with_old_years():
    urls = [
        "https://www.wichita.edu/news/2020/story.php",
        "https://www.wichita.edu/admissions/apply.php",
    ]
    result = filter_urls(urls)
    assert "https://www.wichita.edu/news/2020/story.php" not in result
    assert "https://www.wichita.edu/admissions/apply.php" in result


def test_keeps_current_year_urls():
    urls = ["https://www.wichita.edu/events/2026/openhouse67.php"]
    assert filter_urls(urls) == urls


def test_keeps_urls_with_no_year_at_all():
    urls = ["https://www.wichita.edu/dining/pho.php"]
    assert filter_urls(urls) == urls


def test_drops_every_old_year_in_the_list():
    old_years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]
    urls = [f"https://www.wichita.edu/news/{year}/story.php" for year in old_years]
    assert filter_urls(urls) == []
