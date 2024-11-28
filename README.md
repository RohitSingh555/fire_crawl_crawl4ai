# fire_crawl_crawl4ai

**websites.txt store names of websites you want to crawl through**
**crawled_websites.json stores the results for create_sitemap_step_one.py python file**
**cleaned_websites.json stores the results for clean_json python file**
**confirmed_fire_article_links.txt file stores the links to the articles related to fire**
**confirmed_fire_articles_live.json file stores the structured data along with links to the articles related to fire**

Create python env

then install requirements.txt and run the following files in order:

First run this file: *create_sitemap_step_one.py*

then run: *get_last_modified_date.py*

then run: *clean_json.py*

then run: either *crawler_by_umang.py* or *crawler_by_rohit.py* for creating text or json response respectively.


Important files :
*final_crawler.py*

generates:
results_of_fire_incidents_28th_nov.json file