# Narrative Prototype - The French Revolution

[WIP]

This projects aims to be a first prototype on narrative exploration. In particular, the focus of the study is the French Revolution. The idea is to explore events and participants throughout structured ([Wikidata](https://www.wikidata.org)) and unstructured ([Wikipedia](https://www.wikipedia.org)) data. Structured data can help better grasp the main entities, objects or events, while unstructured data like text can help make hypotheses on how events are linked.

This project is currently undergoing in the framework of [MUHAI European Project](https://www.muhai.org/). 

## Set Up

If using https, run:
```python
git clone https://github.com/SonyCSLParis/building-fr-narrative-from-wikidata.git 
cd building-fr-narrative-from-wikidata
```

If using ssh, run:
```python
git clone git@github.com:SonyCSLParis/building-fr-narrative-from-wikidata.git
cd building-fr-narrative-from-wikidata
```

In the `settings` folder, create a `private.py`file and add the following paramters:
* ROOT_PATH: root path to the project directory
* AGENT: your user agent that you can find on the web.


Version of Python used: 3.9.4

Create a virtual env and activate it (example below with conda)
```bash
conda create -n <yourenvname> python=3.9.4
conda activate <yourenvname>
```

```bash
pip install -r requirements.txt
```

Later when launching the app, you might encounter the following error:
```bash
ImportError: pycurl: libcurl link-time ssl backends (secure-transport, openssl) do not include compile-time ssl backend (none/other)
```

To prevent this error, and following [this link](https://stackoverflow.com/questions/21096436/ssl-backend-error-when-using-openssl), you can run the followings:
```bash
pip uninstall pycurl
export PYCURL_SSL_LIBRARY=openssl
pip install pycurl --no-cache-dir
```

Then run the following:
```bash
python setup.py install
```


Finally, to run the streamlit app
```bash
cd app-demo && streamlit run app.py
```




## Structure

- [app-demo](./app-demo)

  Streamlit web application to collect data and build networks.

- [graph_building](./graph_building)

  Module to build networks using networkx or pyvis.

- [settings](./settings)

- [kb_sparql](./kb_sparql) 
  
  Using a SPARQL wrapper to query wikidata, as well as the knowledge graph created throughout the process.

- [wikipedia_narrative](./wikipedia_narrative)

    Used for the pilot: mapping Wikidata/Wikipedia, extracting infoboxes and text from Wikipedia


## Citation
If using this work, please cite the following:

```<to-be-completed>```