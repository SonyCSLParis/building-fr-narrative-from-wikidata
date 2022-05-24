import os
import yaml
import unittest
from settings.settings import ROOT_PATH
from wikipedia_narrative.data_loader import EventDataLoader
from wikipedia_narrative.pipeline import NarrativePipeline

text_1 = "The Coup of 18 Brumaire brought General Napoleon Bonaparte to power as First Consul of France" + \
         "and in the view of most historians ended the French Revolution."
text_2 = "This bloodless coup d'état overthrew the Directory, replacing it with the French Consulate." + \
         "This occurred on 9 November 1799, which was 18 Brumaire, Year VIII under the French Republican calendar."

  
class ConfigPipelineTest(unittest.TestCase):
  
    def test_data_loader(self):
        with self.assertRaises(ValueError):
           EventDataLoader(granularity=True, titles=True, context=True)
        with self.assertRaises(ValueError):
           EventDataLoader(granularity="sections", titles="True", context=True)
        with self.assertRaises(ValueError):
           EventDataLoader(granularity="sections", titles=True, context="True")
        
        try:
            EventDataLoader(granularity="sections", titles=True, context=True)
        except:
            self.fail("EventDataLoader()raised ExceptionType unexpectedly")

    def test_pipeline_params(self):
        pass
    
    def test_pipeline_docs(self):
        with open(os.path.join(ROOT_PATH, "wikipedia_narrative/config.yaml"), "r") as file:
            config=yaml.load(file, Loader=yaml.FullLoader)

        pipeline = NarrativePipeline(pipeline_config=config)

        with self.assertRaises(TypeError):
            pipeline([])
        
        with self.assertRaises(TypeError):
            pipeline({1: text_1, 2: text_2})
        
        with self.assertRaises(TypeError):
            pipeline([text_1, [text_2]])
        
        with self.assertRaises(TypeError):
            pipeline([(text_1), [text_2]])
        
        with self.assertRaises(TypeError):
            pipeline([(text_1, {"id": 1}), ([text_2], {"id": 2})])
        
        try:
            pipeline([text_1, text_2])
        except:
            self.fail("pipeline()raised ExceptionType unexpectedly")
        
        try:
            pipeline([(text_1, {"id": 1}), (text_2, {"id": 2})])
        except:
            self.fail("pipeline()raised ExceptionType unexpectedly")
  
if __name__ == '__main__': 
    unittest.main()

