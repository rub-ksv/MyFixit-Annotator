#   MyFixit Annotator            
            
MyFixit Annotator is a web-based app for the annotation of steps in [MyFixit dataset](https://github.com/rub-ksv/MyFixit-Dataset) with the required tool, disassembled parts, and removal verbs.              

The annotation guideline and the details of the dataset are introduced in [our LREC paper.](http://www.lrec-conf.org/proceedings/lrec2020/pdf/2020.lrec-1.260.pdf)          
            
The app is optimized to speed up the annotation by the following means:            
            
 - Using an unsupervised method for the extraction and suggestion of required tools, based on the Jaccard distance between the bags of n-grams in text.  
               
 - For the extraction of disassembled parts, either of the following methods can be selected, according to the amount of labeled data:            
   1. A state-of-the-art supervised approach with a BiLSTM-CRF based sequence labeling architecture, trained with contextualized embeddings ([reference paper](https://www.aclweb.org/anthology/N19-1078.pdf)).              
   2. A simple unsupervised approach which operates by shallow parsing of the sentences and extracting the noun and verb phrases. The parser is powered by a hierarchical BiLSTM-CRF architecture trained on the Conll-2000 corpus ([reference paper](https://www.aclweb.org/anthology/C18-1139.pdf)). The noun phrases will be further filtered using Wordnet, and a noun is suggested if any of its noun synsets have 'artifact' in its hypernyms. It also keeps track of the annotated parts and verbs during the annotation and suggests those parts/verbs in future steps. In addition, it splits the sentences of the annotated steps and uses the annotation of sentences for the next steps during the annotation.            
            
## Reqirements            
            
Before running the app, check the values in [constants.py](src/web_app/constants.py) for the path to the root, STATIC_FOLDER, the MongoDB address, and port. You need a running MongoDB server with the loaded database. The app directly reads and writes the annotation from/to the database. 

**The annotated database and the processes data required for the annotator can be downloaded from [here](https://github.com/rub-ksv/MyFixit-Dataset).**  

For learning about MongoDB installation, please refer to its [documentation](https://docs.mongodb.com/manual/installation/).

After downloading the JSON files, you can import them into the database by the following command:

    mongoimport --db myfixit --collection posts --file <fileName>.json   
    
**Main required libraries:**   
> nltk, flair, flask, inflect, pymongo   


## How to Run            
    python3 run.py

The app will be listening on the default host. To access it type the address in your browser:

    http://127.0.0.1:5000

Tested with Python 3.6.7
            
## How It Works            
  
### Selecting the Device Category and the Extraction Method, and Loading the Data  
On the first page, you can choose the category of devices for annotation, either by clicking on the buttons or writing the name of category or subcategory in the textbox.    
If the labeled data is available in that category, you can select to use the supervised sequence labeling method (BILSTM-CRF):             
            
![Category selection](src/web_app/static/images/category_selection.png?raw=true)            
            
The annotator first checks if the processed data (part/verb/tool candidates) for the selected category and the method, i.e., supervised (deep) or unsupervised (basic), exist in `src/web_app/tables`. If not, it queries the database for the relevant manuals and gathers all their steps with unique text descriptions. Among the gathered steps, the ones which are already annotated will be removed from the annotation queue. In th eprocess of producing the tables, it downloads the images of each step and tool in the static folder.    
You can use the [existing tables](https://github.com/rub-ksv/MyFixit-Dataset) and skip the heavy process of parsing/tagging for extracting the part/verb candidates. In that case, select the ***Only download images*** checkbox so that the app only downloads the steps/tools images without generating the tables.               

- **If the supervised model is selected**, the app checks if a trained sequence labeling model for the chosen category exists in `/src/part_extraction/models/`; if not, it will automatically train the model from the annotated steps of the selected category in the database.
            
- **If the unsupervised model is selected**, the app looks into the already annotated steps and tokenizes their sentences (a step can have several sentences). For each sentence and having the word-level annotation, it produces a dictionary of sentence-level annotations. While converting the word-level annotation of steps to sentence-level, the reference point for the span of the words changes from the beginning of the step to the beginning of the sentence. Apart from the sentence-level annotations, it produces a set of all removal verbs and detachable parts from the annotated data. These words plus the ones that you select during the annotation will be written into the `web_app/resources/detachable_objs.txt` and `web_app/resources/removal_verbs.txt`. This information will be used later during the annotation.            
  
  
### Anotation Scheme  
  
Here is a screenshot of the annotation page:            
            
![App screenshot](src/web_app/static/images/step.png?raw=true)      
   
#### Word Level Verbs            
In the basic model, for the word-level verbs `(section 1 in the screenshot)`, if a verb exists in the set of removal verbs, its checkbox will be checked by default. Also, when we select a verb during the annotation, the verb would be added to the set of removal verbs, and it will be checked in the next steps. Therefore, as we proceed with annotation, the app suggests more verbs.  
            
#### Verb Indexes            
For the verb indexes `(section 2)`, if the number of selected verbs and selected parts are equal, the verb will be indexed automatically by its corresponding part, i.e., the first verb with the first part and so on. Still, if we manually enter the indexes, it would be overwritten.            
            
#### Word Level parts            
In the basic model and for the word-level part `(section 3)`, after producing a list of noun phrases and filtering them by Wordnet, you see them as the checkboxes.  If Wordnet does not have some parts or in case of the parser's mistake, you can enter the part's name manually in the textbox beneath the checkboxes. **The span of the words can be entered either in the form of beginning-end or just the beginning**. Similar to the word-level verbs, the parts added to the set of "detachable parts" will be checked by default. Also, when we manually enter a Wordnet filtered part in the textbox, it also will be added to the set of detachable parts and Wordnet filtering will not remove it in the next steps.            
            
#### Step Level parts   
Step level annotation is considered for the steps that the word-level annotation cannot represent the disassembled part, e.g., when we have noun ellipsis or implicit detachment of the parts. In such cases, please write the complete name of the disassembled part in `(section 4)`.    
  
#### Extending the Sentence-level Annotations to New Steps            
            
The basic model uses sentence-level annotation for the annotation of steps that contain those annotated sentences. There is an assumption here that the annotation of a sentence is independent of its surrounding sentences. Even if the full description of the two steps is different, they still might have some common sentences.            
            
If a step includes a sentence that is already annotated, this sentence will be shown in `section 6` of the screenshot. The presented example in the screenshot is the last sentence of the step, which is removed from the description. The spans are also changed automatically, referring to the beginning of this step. After submitting the annotation, the selected parts and the existing annotations will be combined together, while the parts' indexes and spans will be fixes automatically according to the parts that are selected after and before the annotated ones. When we annotate a step, the app uses its sentence-level annotation also for future steps, and as we proceed with annotation, we will have fewer sentences to read.  
There is also a checkbox on the bottom of the page that if you select it, the app will not use the previous annotations.   
#### Tool Annotation            
            
            
The tool annotation is in `section 5` in which the tools in the manuals toolbox are the checkbox candidates. The unsupervised method proposed in the paper is used for the tool extraction, and the extracted tools will be checked by default.                        
            
#### Submitting            
After pressing the submit bottom, the app checks the inputs to make sure all fields are entered as they are expected. It checks if the number of verb indexes matches the number of selected verbs and if the span of selected words matches the words in the text. If everything is correct, it updates the annotation of all the steps with identical full text, and redirects to the next step, while on the screen you can see how many steps are updated with which information in the previous step `(section 7)`.

## Further Reading
[Why can’t we fix our own electronic devices?](https://theconversation.com/why-cant-we-fix-our-own-electronic-devices-77601)   
[Reduce, reuse, reboot: why electronic recycling must up its game](https://www.theguardian.com/environment/2017/nov/20/electronic-recycling-e-waste-2017-gadgets)  
[Why repairing electronics will fix our environment?](https://medium.com/if-you-want-to/repair-electronics-to-fix-our-environment-12f693d55754)

# Cite
If you found our work useful, please cite:

    @InProceedings{nabizadeh-kolossa-heckmann:2020:LREC,
      author    = {Nabizadeh, Nima  and  Kolossa, Dorothea  and  Heckmann, Martin},
      title     = {MyFixit: An Annotated Dataset, Annotation Tool, and Baseline Methods for Information Extraction from Repair Manuals},
      booktitle      = {Proceedings of The 12th Language Resources and Evaluation Conference},
      month          = {May},
      year           = {2020},
      address        = {Marseille, France},
      publisher      = {European Language Resources Association},
      pages     = {2120--2128}}
