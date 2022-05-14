from pickle import TRUE
import sys
from turtle import title
from urllib.request import urlopen
from bs4 import BeautifulSoup
from mdutils.mdutils import MdUtils
from mdutils import Html
import validators
from timeit import default_timer as timer
import os
import requests
import uuid

DOWNLOAD_PIC = True
SHORT_SUFFIX = '.md'
SUFFIX = '.markdown'

def print_with_space(s):
    print()
    print(s)
    print()

if __name__ == "__main__":
    start_time = timer()
    argvs = sys.argv

    if len(argvs) != 3:
        print_with_space("Incorrect Usage: The command line accepts exactly two arguments.\n" +
                        "The first is the WeChat article's URL. HTTP prefix (https:// or http://) is optional\n" + 
                        "The second is filename for the output Markdown file. Markdown suffix (.md or .markdown) is optional\n" +
                        "Example: python3 wechat2md.py mp.weixin.qq.com/s/foobar foobar")
        sys.exit()

    article = argvs[1]
    filename = argvs[2]

    # Remove suffix, if any
    if filename.endswith('.md'):
        filename = filename[:len(filename) - len(SHORT_SUFFIX)]
    if filename.endswith('.markdown'):
        filename = filename[:len(filename) - len(SUFFIX)]

    # Redownload pictures can be very time-consuming. Ask if needs to be regenerated.
    if os.path.exists('out/' + filename + '.markdown') and os.path.exists('assets/' + filename):
        regen_cmd = input("You have generated " + filename + " before.\n Do you want to regenerate it? (y/n): ")
        print(regen_cmd)
        if regen_cmd.lower() == 'y' or regen_cmd.lower() == 'yes':
            # delete current article and assets
            print_with_space("Delete current resources for regeneration...")
            os.remove('out/' + filename + '.markdown')
            dir = 'assets/' + filename
            for img in os.listdir(dir):
                os.remove(dir + '/' + img)
        else:
            sys.exit()

    if not article.startswith("https://") and not article.startswith("http://"):
        article = "https://" + article

    if not validators.url(article):
        print_with_space("Not a valid URL\n无效URL链接")
        sys.exit()

    if "mp.weixin.qq.com" not in article:
        print_with_space("URL is not on the WeChat Official Accounts Platform!\n文章不在微信公众平台上")
        sys.exit()

    page = urlopen(article)
    html_res = page.read().decode("utf-8")

    title = None
    author = None
    account_name = None
    date_time = None

    bs = BeautifulSoup(html_res, "html.parser")
    article_div = bs.find("div", {"id": "js_article"})

    if article_div is None:
        print_with_space("Cannot find the article. Please make sure the URL is valid")
        sys.exit()

    print_with_space("Article fetched. Conversion begin...")
    # Title
    title_elem = article_div.find("h1", {"class": "rich_media_title", "id": "activity-name"})
    if title_elem is not None:
        title = title_elem.get_text().strip()
    else:
        print_with_space("[Warning]: Cannot find the article's title")

    # Metadata
    metadata = article_div.find("div", {"class": "rich_media_meta_list", "id": "meta_content"})

    author_elem = metadata.find("span", {"class": "rich_media_meta rich_media_meta_text"})
    if author_elem is not None:
        author = author_elem.get_text().strip()
    else:
        print_with_space("[Warning]: Cannot find the article's author")

    account_name_elem = metadata.find("strong", {"class": "profile_nickname"})
    if account_name_elem is not None:
        account_name = account_name_elem.get_text().strip()
    else:
        print_with_space("[Warning]: Cannot find the article's account name")

    #TODO: extract date from metadata

    # Add header
    md_content = "# **" + title + "**\n"
    md_content = md_content + "### Author: " + str(author) + " | Account: " + str(account_name) + "\n\n"

    # Content: make sure find the one in the body
    wrapper = article_div.find("div", {"class": "rich_media_wrp"})
    content_div = wrapper.find("div",  {"id": "js_content"})

    
    for div in content_div.find_all(recursive=False):
        text = div.get_text().strip()

        img_div = div.find('img')
        
        if img_div:
            if not DOWNLOAD_PIC or not img_div.has_attr('data-src'):
                continue
            href = img_div['data-src']
            res = requests.get(href.strip())

            pic_name = uuid.uuid4().hex + '.png'
            
            # Create assets/ directory for the first time
            if not os.path.isdir("./assets"):
                os.mkdir('assets')

            # Create asset directory for the article being converted
            if not os.path.exists("assets/" + filename):
                os.mkdir('assets/' + filename)

            pic = open('./assets/' + filename + '/' + pic_name, "wb")
            pic.write(res.content)
            pic.close()
            print("Image saved: " + pic_name)

            path_name_str = '"../assets/' + filename + '/' + pic_name + '"'
            # TODO: make the image size relative to the screensize
            md_content = md_content + '\n<center><img style="border-radius: 0.3125em; box-shadow: 0 2px 4px 0 rgba(34,36,38,.12),0 2px 10px 0 rgba(34,36,38,.08);" src=' + path_name_str + '></center>\n\n'
            
        else:
            if not text:
                continue
            md_content = md_content + str(div) + "\n\n"

    
    if not os.path.isdir("./out"):
        os.mkdir("out")

    # Add MD suffix
    filename += '.markdown'
    with open("./out/" + filename, 'w') as f:
        f.write(md_content)

    end_time = timer()
    print_with_space("Article converted: " + title)
    print("Success! Time taken: {0:.2f}s".format(end_time - start_time))
    print("View the markdown file: " + os.path.abspath("./out/" + filename))
