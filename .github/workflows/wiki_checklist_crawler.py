from urllib.request import urlopen
from urllib.parse   import urlencode
import json
import argparse
import pathlib
import pprint


def askWikiAPI(url, query):
    payload = {'action': 'ask', 
               'format': 'json',
               'errorlang': 'uselang',
               'query': query}
    payload_string = urlencode(payload)
    
    with urlopen('?'.join([url + "/api.php", payload_string])) as response:    
        if (response.status != 200):
            raise Exception("Wiki API returned {}".format(response.status))
        return json.load(response)

def createQueryString(keys):
    return ' | '.join(['[[{key}::+]]|?{key}'.format(key=key) for key in keys]) + '|limit=3'

def extractTextFromRequest(response, add_source_link=False):
    outDict = {}
    for pagekey, page in response['query']['results'].items():
        pageDict = {}

        if(add_source_link):
            pageDict['source_link'] = page['fullurl']

        for propertykey, property in page['printouts'].items():
            # media wiki changes '_' and capitalization -.-*
            pageDict[propertykey.replace(' ', '_').lower()] = [entry['fulltext'] for entry in property]
            
        outDict[pagekey] = pageDict
    return outDict
        
def writeMarkdownFiles(path, checklist_data, metadata, text, add_source_link=False):
    for pagename, page in checklist_data.items():
        with open(path / ''.join([makePOSIXfilename(pagename),'.md']), 'w') as f:
            f.write('---\n')

            if(add_source_link):
                f.write('source_link: {}\n'.format(page['source_link']))
            
            for propertyname, property in page.items():
                if propertyname not in metadata:
#                     print("{} not found in {}".format(propertyname, metadata_keys))
                    continue
                if len(property) == 1:
                    f.write('{}: {}\n'.format(propertyname, property[0]))
                else:
                    f.write('{}: \n'.format(propertyname))
                    for line in property:
                        f.write('  - {}\n'.format(line))
            
            f.write('---\n\n')
            
            for propertyname, property in page.items():

                if propertyname not in text:
#                     print("{} not found in {}".format(propertyname, text_keys))
                    continue
                f.write('# {}\n'.format(text[propertyname]))
                for line in property:
                    f.write('* {}\n'.format(line))
                f.write("\n")
                
def makePOSIXfilename(filename):
    safeFilenameChars = ['_', '-', '.']
    return "".join([c if c.isalnum() or c in safeFilenameChars else '_' for c in filename])

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Pulling Semantic Media Wiki properties and writing them into a pandoc Markdown file')
    parser.add_argument('-u', '--url', dest='url', required=True,
                        help='Wiki page url to request')
    parser.add_argument('-m', '--meta', dest='meta', 
                        action='extend', nargs='+', metavar='META-PROPERTY',
                        help='Wiki properties to add to YAML header.\
                              If multiple entries are found, they\'ll be added as a list.')
    parser.add_argument('-t', '--text', dest='text', 
                        action='append', nargs=2,
                        metavar=('HEADING', 'TEXT-PROPERTY'),
                        help='Wiki properties to add as text section.\
                              Section name will be used as heading.\n \
                              Can be called multiple times to add more text properties.\
                              If a property is found multiple times they are added as new lines.')
    parser.add_argument('-o', '--out', dest='path', type=pathlib.Path, default='./',
                        metavar='OUTPUTPATH',
                        help='Optional output path.')
    parser.add_argument('--source_link', dest="source_link", action='store_true',
                        help="Write the source link into the metadata header as 'source_link'")
    
    args = parser.parse_args()
    
#     print(args.url)
    
    # creating a dict for text section headings
    text_headings = {text[1]:text[0] for text in args.text}
#     print([key for key in text_headings])
    
    query = createQueryString(args.meta + [key for key in text_headings])
    # print(query)
    
    response = askWikiAPI(args.url, query)
    # pprint.pprint(response)
    
    checklist_data = extractTextFromRequest(response, args.source_link)
    # pprint.pprint(checklist_data)
    
    writeMarkdownFiles(args.path, checklist_data, args.meta, text_headings, args.source_link)
