# XDAI

Paper | [中文版]()

XDAI is maintained by the Knowledge Engineering Group of Tsinghua University, and supported by Zhipu.AI & Biendata, which is a tuning-free framework for exploiting pre-trained language models in knowledge grounded dialogue. Employing large-scale models including [GLM](https://github.com/THUDM/GLM) and [CPM](https://github.com/TsinghuaAI/CPM-1-Generate), XDAI provides a basic open-domain dialogue generation service (XDAI-open) and several tools for developers in building domain-specific chatbots (XDAI-domain). 



We summarize the features of XDAI as follows:

* Quick Start:  XDAI provide an open-domain knowledge-grounded dialogue service with sufficient ready-to-use open-domain knowledge resources from [XLore2](https://www.xlore.cn/). Developers can easily deploy a dialogue system with this basic service.
* Efficient Inference：Compared with other dialogue systems, XDAI utilizes a novel prompt pattern with knowledge injection, which optimizes the generated dialogues from PLMs without further training or tuning.
* Customized Deployment: For domain-specific developers XDAI provides easy-to-change plugins to enable automatically searching and updating the external knowledge only from a few domain-specific seeds. 
* Incremental Modification: XDAI also  provides a series of toolkits for incremental developing, encouraging developers to refine and customize their personalized components. 

## News ‼️

* The XDAI domain-specific knowledge exploration toolkits are refined !!
* More Language models are accessible now !!

* Our paper is submitted to KDD2022 Applied Data Science track !!

## Architecture

The overall architecture of XDAI is shown as bellow.

![XDAI Framework](pics/framework-XDAI.png)

XDAI consists of two subsystems: online dialogue generation system & offline knowledge curation. Developers can employ XX and XX for local implementation.

(TBD) Details About XDAI Component

### Toolkit

####  PLM API (GLM)
You can deploy your own PLM server by taking the following steps.
We offer the pack of *GLM* version in `tools/PLM`
1. Setup the environment (refer to https://github.com/THUDM/GLM). 
2. Modify the `[PLM]`section in `config/conf.ini`:
    ```ini
    [PLM]
    ip_address = <server_ip>
    glm_port = <self-defined available port>
    glm_api = http://{ip_address}:{glm_port}/glm
    ```
3. Start the server by running:   
    ```shell
    bash tools/deploy_plm.sh
    ```
4. If you use ready-made API, just set `glm_api=<ready-made-PLM-api>` and then add the corresponding function in `module/use_plm`

#### Knowledge Explore
While open-corpus is available, it is also encouraged to setup your own knowledge base.

The knowledge exploration toolkit at `tools/knowledge` is based on https://github.com/luogan1234/concept-expansion-snippet 

Run the script to initiate model:
```shell
bash tools/init_knowledge_explore.sh
```
You can set the topic and seed concepts in `data/seed_concept.json`, and run the task:

```shell
# For init seed concepts
python tools/knowledge/explore.py -t init -f tools/knowledge/data/seed_concept.json
# For periodic knowledge exploration 
python tools/knowledge/explore.py -t update -f tools/knowledge/data/seed_concept.json -i 1 
```
The parameters are:
```text
-t,--task:  init | update
-f,--config_file: config of the specific topic
-i,--interval: if the task is "update", this set the interval days between two consecutive updates.
```
#### FAQ toolkit
If you deploy your own knowledge exploration module as described above, you have to build a retrieval service.

We provide a faq toolkit based on `fuzzybert` which can be attached to the mongodb you use.
Modify the `faq_port` in `TOOL` section in `config/conf.ini` and start the service:
```shell
bash tool/deploy_faq.sh
```

#### Sentence similarity
Modify the `sentsim_port` in `TOOL` section in `config/conf.ini` and start the service:
```shell
bash tool/deploy_sentsim.sh
```
You can also change the `sbert-model` used from https://huggingface.co/models?library=sentence-transformers


#### QA-generation (based on T5)
If you want to use T5-based question generation instead of template-based, you have to build a generation service, which is based on https://github.com/patil-suraj/question_generation.

We provide a QA-gen toolkit, and you should modify the `qagen_port` in `TOOL` section in `config/conf.ini` and start the service:
```shell
bash tool/deploy_t5QA.sh.sh
```
It is required that transformer==3.0.0, as the source code's demand.
This question generation code only supports English question generation, so we use youdao translation for English-Chinese translation, which is implemented in utils/translate.py. This translation interface has a sending limit. If you need to use it, please replace it with your own translation interface.
## Get Started

#### 1. Requirements
```
pip install -r requirements.txt
```
#### 2. Set up PLM API

Get a ready-made PLM generation api or deploy one with the toolkit mentioned above.

#### 3. Design your Bot Agent

You can add agent classes in `agents/` , with one base class in `agents/agent_base.py` three examples offered.
```shell
agents/
├── agent_base.py
├── __init__.py
├── xdai_glm.py
├── xdai_kg.py
└── xdai_kg_specific.py
```
Among which:
- `xdai_glm.py`: The baseline implementation without knowledge injected using GLM as the PLM.
- `xdai_kg.py`: GLM + open knowledge injected using [XLore2](https://www.xlore.cn/)
- `xdai_kg_specific.py`:GLM + specific domain knowledge with self-maintained FAQ db.

#### 4. Interact
We provide the following ways to interact with the chatbot:
1. **Terminal**: The simplest way to expeirence the dialogue system, which does not require the api server as the prerequisite.
```shell
bash scripts/run_terminal_chat.sh
```
2. **Streamlit**: It is started with some backend apis deployed. Run the bash:
```shell
bash scripts/run_streamlit.sh
```
For more information & instruction : https://docs.streamlit.io/ 

3. **Wechaty**: 

Link the chatbot to your wechat account, with backend server required as well.
Before start, you need to get a token from http://wechaty.js.org/ and set the token in `conf.ini`.
Then you can run:
```shell
bash scripts/run_wechaty.sh
```

## Analysis & Example

XDAI can achieve competitive results in both open-domain and domain-specific dialogue scenarios. The table shows 95% confidence intervals for human evaluation results of open-domain dialogue generation.

![Overall](pics/evaluation.png)

There is a case of how the explored knowledge help lifting the informativeness of generated dialogues.

![Overall](pics/case.png)

## Reference

* To be done
