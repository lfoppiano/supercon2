from bs4 import BeautifulSoup

XML_TEMPLATE = """<tei xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc xml:id="_0">
            <titleStmt/>
            <publicationStmt>
                <publisher>Luca Foppiano et al. </publisher>
                <availability>
                    <licence target="https://creativecommons.org/licenses/by-nc/3.0/">
                        <p>CC BY NC 3.0</p>
                    </licence>
                </availability>
            </publicationStmt>
            <sourceDesc>
                <idno type="DOI"/>
            </sourceDesc>
        </fileDesc>
        <encodingDesc>
            <appInfo>
                <application version="0.5.0" ident="grobid-superconductors">
                    <ref target="https://github.com/lfoppiano/grobid-superconductors">A machine learning software for extracting materials and their properties from scientific literature.</ref>
                </application>
            </appInfo>
        </encodingDesc>
        <profileDesc>
            <abstract/>            
        </profileDesc>
    </teiHeader>
    <text xml:lang="en">
        <body/>
    </text>
</tei>"""

def get_text(soup):
    children = soup.findChildren('text')
    return children[0] if children is not None and len(
        children) > 0 else None


def transform_in_tei(sentences, biblio):
    soup = BeautifulSoup(XML_TEMPLATE, 'xml')

    body = get_text(soup).body
    paragraph = soup.new_tag('p')
    body.append(paragraph)

    for sentence in sentences:
        spans = sentence['spans']
        text = sentence['text']

        tag = BeautifulSoup('<s>' + text + '</s>', 'xml')
        paragraph.append(tag)

    return str(soup)