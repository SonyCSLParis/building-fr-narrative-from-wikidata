import re
import wikipedia
from collections import defaultdict

class WikipediaPage:

    def __init__(self, title:str = None, content: str = None, **additional_content: dict):
        """ Wikipedia Page Content from either
        1. title -> tries to find the corresponding wikipedia page
        2. title + content -> directly setting the content to the input content"""
        self.url = None

        if not title:
            raise ValueError("Either `title`, or `title` and `content` should be specified")

        if not content:
            try:
                page = wikipedia.page(title)
            except Exception as e:
                print(e)
                raise ValueError("Could not get the page from title")
            
            self.title = page.title
            self.content = page.content
            self.url = page.url
        
        else:
            self.title = title
            self.content = content
        
        self.section_title = defaultdict(list)
        self.lines = [line for line in self.content.split("\n") if line != '']

        # Preprocessing noisy content
        self.noisy_sections = ["References", "External links", "See also", "Further reading",
                               "Notes", "Sources", "Bibliography", "Footnotes",
                               "Notes and references"]
        self.noisy_pattern = "== {} ==(([^=]|\\s)+((\\s)*==|)|)"

        self.content_filtered = self._preprocess_content_for_pipeline(content=self.content)
        self.lines_filtered = [line for line in self.content_filtered.split("\n") if line != '']

        # Any additional content data for the context
        self.additional_content = additional_content if additional_content else dict()

    
    def _get_sections(self, title: str, lines: list[str], nb: int):
        """ Extract sections from wikipedia text content
        Using lines delimitations as helpers """
        self.section_title[nb-2].append(title)
        sub_sections = [[]]
        for line in lines:
            if line.strip().startswith("="*nb) and (not line.strip().startswith("="*(nb+1))):
                sub_sections.append(list())
            sub_sections[-1].append(line.strip())
        
        sections = dict(title=title, main='\n'.join(sub_sections[0]))
        for index, sub_section in enumerate(sub_sections[1:]):
            sections[index+1] = self._get_sections(title=sub_section[0].replace("="*nb, ""),
                                                   lines=sub_section[1:],
                                                   nb=nb+1)
        
        return sections
    
    def get_sections(self):
        self.sections = self._get_sections(title=self.title, lines=self.lines, nb=2)
    
    def _preprocess_content_for_pipeline(self, content: str):
        """ Remove noisy content (e.g. references/notes etc) """
        for section in self.noisy_sections:
            m = re.search(self.noisy_pattern.format(section), content)
            if m:
                content = content.replace(m.group(0), "==")
        return content
    
    def format_data_for_pipeline(self, granularity: str, titles: bool, nb=2):
        """ Retrieve data in good format for Spacy pipeline """
        context = defaultdict(lambda: None)
        context.update(self.additional_content)
        context['page'] = self.title

        if granularity == 'event':
            if titles:
                return [(self.content_filtered.replace("=", ""),
                         context)]
            else:
                return [('\n'.join([line for line in self.lines_filtered if not line.startswith("==")]),
                         context)]
            
        else:  # granularity = 'section'
            sub_sections = [[]]
            for line in self.lines_filtered:
                if line.strip().startswith("="*nb) and (not line.strip().startswith("="*(nb+1))):
                    sub_sections.append(list())
                sub_sections[-1].append(line.strip())
            data = [('\n'.join(sub_sections[0]), context)]
            for index, section in enumerate(sub_sections[1:]):
                curr_context = context.copy()
                curr_context["section"] = section[0].replace("=", "")
                curr_context["section_nb"] = index + 1
                if titles:
                    data.append(('\n'.join(section[1:]).replace("=", ""),
                                 curr_context))
                else:
                    data.append(('\n'.join([line for line in section[1:] if not line.startswith("===")]).replace("=", ""),
                                 curr_context))

        return data

if __name__ == '__main__':
    page = WikipediaPage("Women's March on Versailles")

    print(page.content)
    print('########')
    print(page.format_data_for_pipeline(granularity='event', titles=True))