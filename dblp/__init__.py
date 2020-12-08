import requests
from lxml import etree
from collections import namedtuple
from time import sleep

DBLP_BASE_URL = 'http://dblp.uni-trier.de/'
DBLP_AUTHOR_SEARCH_URL = DBLP_BASE_URL + 'search/author'

DBLP_PERSON_URL = DBLP_BASE_URL + 'pers/xk/{urlpt}'
# per DBLP staff, rec/conf/... instead of rec/bibtex/conf/... is the "new" format
DBLP_PUBLICATION_URL = DBLP_BASE_URL + 'rec/{key}.xml'

class LazyAPIData(object):
    def __init__(self, lazy_attrs):
        self.lazy_attrs = set(lazy_attrs)
        self.data = None

    def __getattr__(self, key):
        timeoutCount1 = 0
        passFail1 = 0
        # if key fails to return properly, try again (up to 5 times)
        if key in self.lazy_attrs:
            while (passFail1 == 0):
                try:
                    if self.data is None:
                        self.load_data()
                    return self.data[key]
                    passFail1 = 1
                except:
                    if (timeoutCount1 < 5):
                        passFail1 = 0
                        timeoutCount1 = timeoutCount1 + 1
                    else:
                        print("ERROR 1: failed to connect to DBLP 5+ times for"+str(self.urlpt)+", skipping")
                        sleep(1 * timeoutCount1)
                        passFail1 = 1
        raise AttributeError(key)

    def load_data(self):
        pass

class Author(LazyAPIData):
    """
    Represents a DBLP author. All data but the author's key is lazily loaded.
    Fields that aren't provided by the underlying XML are None.

    Attributes:
    name - the author's primary name record
    publications - a list of lazy-loaded Publications results by this author
    homepages - a list of author homepage URLs
    homonyms - a list of author aliases
    """
    def __init__(self, urlpt):
        self.urlpt = urlpt
        self.xml = None
        super(Author, self).__init__(['name','publications','homepages',
                                      'homonyms'])

    def load_data(self):
        self.urlpt.encode('utf-8')
        timeoutCount2 = 0
        passFail2 = 0
        while (passFail2 == 0):
            try:
                resp = requests.get(DBLP_PERSON_URL.format(urlpt=self.urlpt.encode('utf-8')))

                # TODO error handling
                resp.content.encode('utf-8')
                xml = resp.content
                xml.encode('utf-8')
                self.xml = xml
                root = etree.fromstring(xml)
                data = {
                    'name':root.attrib['name'],
                    'publications':[Publication(k) for k in 
                                    root.xpath('/dblpperson/dblpkey[not(@type)]/text()')],
                    'homepages':root.xpath(
                        '/dblpperson/dblpkey[@type="person record"]/text()'),
                    'homonyms':root.xpath('/dblpperson/homonym/text()')
                }

                self.data = data

                passFail2 = 1
            # if connection times out or string is empty, try again until it works or failed 5 times
            except:
                if (timeoutCount2 < 5):
                    passFail2 = 0
                    timeoutCount2 = timeoutCount2 + 1
                else:
                    print("ERROR 2: failed to connect to DBLP 5+ times for: "+str(self.urlpt)+", URL: "+DBLP_PERSON_URL.format(urlpt=self.urlpt.encode('utf-8'))+", skipping")
                    sleep(1 * timeoutCount2)
                    passFail2 = 1

def first_or_none(seq):
    try:
        return next(iter(seq))
    except StopIteration:
        pass

Publisher = namedtuple('Publisher', ['name', 'href'])
Series = namedtuple('Series', ['text','href'])
Citation = namedtuple('Citation', ['reference','label'])

class Publication(LazyAPIData):
    """
    Represents a DBLP publication- eg, article, inproceedings, etc. All data but
    the key is lazily loaded. Fields that aren't provided by the underlying XML
    are None.

    Attributes:
    type - the publication type, eg "article", "inproceedings", "proceedings",
    "incollection", "book", "phdthesis", "mastersthessis"
    sub_type - further type information, if provided- eg, "encyclopedia entry",
    "informal publication", "survey"
    title - the title of the work
    authors - a list of author names
    journal - the journal the work was published in, if applicable
    volume - the volume, if applicable
    number - the number, if applicable
    chapter - the chapter, if this work is part of a book or otherwise
    applicable
    pages - the page numbers of the work, if applicable
    isbn - the ISBN for works that have them
    ee - an ee URL
    crossref - a crossrel relative URL
    publisher - the publisher, returned as a (name, href) named tuple
    citations - a list of (text, label) named tuples representing cited works
    series - a (text, href) named tuple describing the containing series, if
    applicable
    """
    def __init__(self, key):
        self.key = key
        self.xml = None
        super(Publication, self).__init__( ['type', 'sub_type', 'mdate',
                'authors', 'editors', 'title', 'year', 'month', 'journal',
                'volume', 'number', 'chapter', 'pages', 'ee', 'isbn', 'url',
                'booktitle', 'crossref', 'publisher', 'school', 'citations',
                'series'])

    def load_data(self):
        self.key.encode('utf-8')
        timeoutCount3 = 0
        passFail3 = 0
        while (passFail3 == 0):
            try:
                resp = requests.get(DBLP_PUBLICATION_URL.format(key=self.key))

                xml = resp.content
                self.xml = xml
                root = etree.fromstring(xml)
                publication = first_or_none(root.xpath('/dblp/*[1]'))
                if publication is None:
                    raise ValueError
                data = {
                    'type':publication.tag,
                    'sub_type':publication.attrib.get('publtype', None),
                    'mdate':publication.attrib.get('mdate', None),
                    'authors':publication.xpath('author/text()'),
                    'editors':publication.xpath('editor/text()'),
                    'title':first_or_none(publication.xpath('title/text()')),
                    'year':int(first_or_none(publication.xpath('year/text()'))),
                    'month':first_or_none(publication.xpath('month/text()')),
                    'journal':first_or_none(publication.xpath('journal/text()')),
                    'volume':first_or_none(publication.xpath('volume/text()')),
                    'number':first_or_none(publication.xpath('number/text()')),
                    'chapter':first_or_none(publication.xpath('chapter/text()')),
                    'pages':first_or_none(publication.xpath('pages/text()')),
                    'ee':first_or_none(publication.xpath('ee/text()')),
                    'isbn':first_or_none(publication.xpath('isbn/text()')),
                    'url':first_or_none(publication.xpath('url/text()')),
                    'booktitle':first_or_none(publication.xpath('booktitle/text()')),
                    'crossref':first_or_none(publication.xpath('crossref/text()')),
                    'publisher':first_or_none(publication.xpath('publisher/text()')),
                    'school':first_or_none(publication.xpath('school/text()')),
                    'citations':[Citation(c.text, c.attrib.get('label',None))
                                 for c in publication.xpath('cite') if c.text != '...'],
                    'series':first_or_none(Series(s.text, s.attrib.get('href', None))
                                           for s in publication.xpath('series'))
                }

                self.data = data

                passFail3 = 1
            # if connection times out or string is empty, try again until it works or failed 5 times
            except:
                if (timeoutCount3 < 5):
                    passFail3 = 0
                    timeoutCount3 = timeoutCount3 + 1
                else:
                    print("ERROR 3: failed to connect to DBLP 5+ times for: "+str(self.key)+", URL: "+DBLP_PUBLICATION_URL.format(key=self.key)+", skipping")
                    sleep(1 * timeoutCount3)
                    passFail3 = 1

def search(author_str):
    author_str.encode('utf-8')
    timeoutCount4 = 0
    passFail4 = 0
    while (passFail4 == 0):
        try:
            resp = requests.get(DBLP_AUTHOR_SEARCH_URL, params={'xauthor':author_str})

            #TODO error handling
            root = etree.fromstring(resp.content)
            arr_of_authors = []
            for urlpt in root.xpath('/authors/author/@urlpt'):
                resp1 = requests.get(DBLP_PERSON_URL.format(urlpt=urlpt))

                xml = resp1.content
                root1 = etree.fromstring(xml)
                if root1.xpath('/dblpperson/homonym/text()'):
                    for hom_urlpt in root1.xpath('/dblpperson/homonym/text()'):
                        arr_of_authors.append(Author(hom_urlpt))
                else:
                    arr_of_authors.append(Author(urlpt))

            passFail4 = 1

        # if connection times out or string is empty, try again until it works or failed 5 times
        except:
            if (timeoutCount4 < 5):
                passFail4 = 0
                timeoutCount4 = timeoutCount4 + 1
            else:
                print("ERROR 4: failed to connect to DBLP 5+ times for: "+str(author_str).encode('utf-8')+", skipping")
                sleep(1 * timeoutCount4)
                passFail4 = 1

    return arr_of_authors
