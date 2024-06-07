"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[5950],{5690:(e,n,a)=>{a.r(n),a.d(n,{assets:()=>c,contentTitle:()=>s,default:()=>u,frontMatter:()=>i,metadata:()=>r,toc:()=>l});var t=a(4848),o=a(8453);const i={},s="Config files",r={id:"config",title:"Config files",description:"A main aim for the sunholo library is to have as much of the functionality needed for GenAI apps available via configuration files, rather than within the code.",source:"@site/docs/config.md",sourceDirName:".",slug:"/config",permalink:"/docs/config",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/config.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"Sunholo CLI",permalink:"/docs/cli"},next:{title:"Databases",permalink:"/docs/databases/"}},c={},l=[{value:"Calling config files",id:"calling-config-files",level:2},{value:"sunholo CLI",id:"sunholo-cli",level:2},{value:"vacConfig",id:"vacconfig",level:2},{value:"agentConfig",id:"agentconfig",level:2},{value:"userConfig",id:"userconfig",level:2},{value:"promptConfig",id:"promptconfig",level:2}];function d(e){const n={a:"a",code:"code",h1:"h1",h2:"h2",p:"p",pre:"pre",...(0,o.R)(),...e.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(n.h1,{id:"config-files",children:"Config files"}),"\n",(0,t.jsxs)(n.p,{children:["A main aim for the ",(0,t.jsx)(n.code,{children:"sunholo"})," library is to have as much of the functionality needed for GenAI apps available via configuration files, rather than within the code."]}),"\n",(0,t.jsx)(n.p,{children:"This allows you to set up new instances of GenAI apps quickly, and experiment with new models, vectorstores and other features."}),"\n",(0,t.jsx)(n.p,{children:"There are various config files available that control different features such as VAC behaviour and user access.  This is very much still a work in progress so the format may change in the future."}),"\n",(0,t.jsx)(n.h2,{id:"calling-config-files",children:"Calling config files"}),"\n",(0,t.jsxs)(n.p,{children:["Use the config functions within ",(0,t.jsx)(n.a,{href:"sunholo/utils/config",children:(0,t.jsx)(n.code,{children:"sunholo.utils"})})," to use the config files within your GenAI application.  The most often used config is ",(0,t.jsx)(n.code,{children:"vacConfig"})," below, which is called like this:"]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:"from sunholo.utils import load_config_key\n\nvector_name = 'pirate_speak'\nllm = load_config_key('llm', vector_name, kind='vacConfig')\n# 'openai'\nagent = load_config_key('agent', vector_name, kind='vacConfig')\n# 'langserve'\n\nvector_name = 'eduvac'\nllm = load_config_key('llm', vector_name, kind='vacConfig')\n# 'anthropic'\nagent = load_config_key('agent', vector_name, kind='vacConfig')\n# 'eduvac'\n"})}),"\n",(0,t.jsxs)(n.p,{children:["You can call your config files anything, just make sure they are in the ",(0,t.jsx)(n.code,{children:"config/"})," folder relative to your working directory, or as configured via the ",(0,t.jsx)(n.code,{children:"_CONFIG_FOLDER"})," environment variable."]}),"\n",(0,t.jsx)(n.h2,{id:"sunholo-cli",children:"sunholo CLI"}),"\n",(0,t.jsx)(n.p,{children:"A CLI command is included to more easily inspect and validate configurations."}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-bash",children:"sunholo list-configs\n#'## Config kind: promptConfig'\n#{'apiVersion': 'v1',\n# 'kind': 'promptConfig',\n# 'prompts': {'eduvac': {'chat_summary': 'Summarise the conversation below:\\n'\n#                                        '# Chat History\\n'\n#                                        '{chat_history}\\n'\n#                                        '# End Chat History\\n'\n#                                        'If in the chat history is a lesson '\n# ...                \n\nsunholo list-configs --kind 'vacConfig'\n## Config kind: vacConfig\n#{'apiVersion': 'v1',\n# 'kind': 'vacConfig',\n# 'vac': {'codey': {'agent': 'edmonbrain_rag',\n# ...\n\nsunholo list-configs --kind=vacConfig --vac=edmonbrain           \n## Config kind: vacConfig\n#{'edmonbrain': {'agent': 'edmonbrain',\n#                'avatar_url': 'https://avatars.githubusercontent.com/u/3155884?s=48&v=4',\n#                'description': 'This is the original '\n#                               '[Edmonbrain](https://code.markedmondson.me/running-llms-on-gcp/) '\n#                               'implementation that uses RAG to answer '\n#                               'questions based on data you send in via its '\n# ...\n\n# add the --validate flag to check the configuration against a schema\nsunholo list-configs --kind=vacConfig --vac=edmonbrain --validate           \n## Config kind: vacConfig\n#{'edmonbrain': {'agent': 'edmonbrain',\n#                'avatar_url': 'https://avatars.githubusercontent.com/u/3155884?s=48&v=4',\n#                'description': 'This is the original '\n#                               '[Edmonbrain](https://code.markedmondson.me/running-llms-on-gcp/) '\n#                               'implementation that uses RAG to answer '\n#                               'questions based on data you send in via its '\n# ...\n#Validating configuration for kind: vacConfig\n#Validating vacConfig for edmonbrain\n#OK: Validated schema\n"})}),"\n",(0,t.jsxs)(n.p,{children:["You can use the ",(0,t.jsx)(n.code,{children:"--validate"})," flag in CI/CD to check the configuration each commit, for example in Cloud Build:"]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-yaml",children:"...\n  - name: 'python:3.9'\n    id: validate config\n    entrypoint: 'bash'\n    waitFor: [\"-\"]\n    args:\n    - '-c'\n    - |\n      pip install --no-cache sunholo\n      sunholo list-configs --validate || exit 1\n"})}),"\n",(0,t.jsx)(n.h2,{id:"vacconfig",children:"vacConfig"}),"\n",(0,t.jsx)(n.p,{children:"This is the main day to day configuration file that is used to set LLMs, databases and VAC tags.  An example is shown here:"}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-yaml",children:'kind: vacConfig\napiVersion: v1\ngcp_config: # reached via vac=\'global\'\n  project_id: default-gcp-project\n  location: europe-west1\nvac:\n  personal_llama:\n    llm: vertex  # using google vertex\n    model: gemini-1.5-pro-preview-0514 # models within google vertex\n    agent: vertex-genai # using VAC created for Vertex\n    display_name: LlamaIndex via Vertex AI # for UI to the end user\n    grounding: # vertex only - add grounding\n      google_search: true\n    memory: # multiple memory allowed\n      - llamaindex-native:\n          vectorstore: llamaindex # only on vertex\n          rag_id: 4611686018427387904 # generated via vertex RAG\n      - agent_data_store:\n          vectorstore: vertexai_agent_builder # only on vertex\n          data_store_id: 1231231231231  # generated via vertex\n    gcp_config:\n      project_id: multivac-internal-dev # default project\n      location: us-central1   # default location\n    chunker: # control chunking behaviour when sending data to llamaindex\n      chunk_size: 1000\n      overlap: 200\n    pirate_speak:\n        llm: openai\n        agent: langserve\n        #agent_url: you can specify manually your URL endpoint here, or on Multivac it will be populated automatically\n        display_name: Pirate Speak\n        tags: ["free"] # for user access, matches users_config.yaml\n        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4\n        description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that will repeat back what you say but in a pirate accent.  Ooh argh me hearties!  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.\n    eduvac:\n        llm: anthropic\n        model: claude-3-opus-20240229\n        agent: eduvac # needs to match multivac service name\n        agent_type: langserve # if you are using langserve instance for each VAC, you can specify its derived from langserve\n        display_name: Edu-VAC\n        tags: ["free"] # set to "eduvac" if you want to restrict usage to only users tagged "eduvac" in users_config.yaml\n        avatar_url: ../public/eduvac.png\n        description: Educate yourself in your own personal documents via guided learning from Eduvac, the ever patient teacher bot. Use search filters to examine available syllabus or upload your own documents to get started.\n        upload:   # to accept uploads of private documents to a bucket\n            mime_types: # pick which mime types got to which bucket\n            - all\n            buckets:\n                all: your-bucket\n        buckets: # pick which bucket takes default uploads\n            raw: your-bucket\n        docstore: # this needs to be valid to have document storage\n            - alloydb-docstore: # you can have multiple doc stores\n                type: alloydb\n        alloydb_config: # example if using alloydb as your doc or vectorstore\n            project_id: your-projectid\n            region: europe-west1\n            cluster: your-cluster\n            instance: primary-instance-1\n    csv_agent:\n        llm: openai\n        agent: langserve\n        #agent_url: you can specify manually your URL endpoint here, or on Multivac it will be populated automatically\n        display_name: Titanic\n        tags: ["free"]\n        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4\n        description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that lets you ask questions over structured data like a database.  In this case, a local database contains statistics from the Titanic disaster passengers.  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.\n    rag_lance:\n        llm: openai\n        agent: langserve\n        display_name: Simple RAG\n        tags: ["free"]\n        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4\n        description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that lets you ask questions over unstructured data.\n        memory: # you can have multiple destinations for your embedding pipelines\n            - lancedb-vectorstore:\n                vectorstore: lancedb\n                read_only: true # don\'t write embeddings to this vectorstore \n    finetuned_model:\n        llm: model_garden # an example of a custom model such as Llama3 served by Vertex Model Garden\n        agent: langserve\n        tags: ["clientA"]\n        gcp_config: # details of the Model Garden endpoint\n            project_id: model_garden_project\n            endpoint_id: 12345678\n            location: europe-west1\n    image_talk:\n        llm: vertex\n        model: gemini-1.0-pro-vision\n        agent: langserve\n        upload: # example of accepting uploads\n            mime_types:\n            - image\n        display_name: Talk to Images\n        tags: ["free"]\n        avatar_url: https://avatars.githubusercontent.com/u/1342004?s=200&v=4\n        description: A picture is worth a thousand words, so upload your picture and ask your question to the Gemini Pro Vision model.  Images are remembered for your conversation until you upload another.  This offers powerful applications, which you can get a feel for via the [Gemini Pro Vision docs](https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal/design-multimodal-prompts) \n    sample_vector:\n        llm: azure # using Azure OpenAI endpoints\n        model: gpt-4-turbo-1106-preview\n        agent: langserve\n        display_name: Sample vector for tests\n        avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4\n        description: An Azure OpenAI example\n        memory: # you can have multiple vectorstore destinations\n            - lancedb-vectorstore:\n                vectorstore: lancedb\n        embedder:\n            llm: azure\n        azure: # your azure details\n            azure_openai_endpoint: https://openai-central-blah.openai.azure.com/\n            openai_api_version: 2024-02-01\n            embed_model: text-embedding-ada-002 # or text-embedding-3-large\n    edmonbrain:\n      llm: openai\n      agent: edmonbrain\n      display_name: Edmonbrain\n      avatar_url: https://avatars.githubusercontent.com/u/3155884?s=48&v=4\n      description: This is the original [Edmonbrain](https://code.markedmondson.me/running-llms-on-gcp/) implementation that uses RAG to answer questions based on data you send in via its `!help` commands and learns from previous chat history.  It dreams each night that can also be used in its memory.\n      model: gpt-4o\n      memory_k: 10 # how many memories will be returned in total after relevancy compression\n      memory:\n        - personal-vectorstore:\n            vectorstore: lancedb\n            k: 10 #  how many candidate memory will be returned from this vectorstore\n        - eduvac-vectorstore:\n            vector_name: eduvac\n            read_only: true # can only read, not write embeddings\n            vectorstore: lancedb\n            k: 3 #  how many candidate memory will be returned from this vectorstore\n'})}),"\n",(0,t.jsx)(n.h2,{id:"agentconfig",children:"agentConfig"}),"\n",(0,t.jsx)(n.p,{children:"This configuration file sets up standard endpoints for each type of agent, corresponding to a VAC running."}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-yaml",children:'# this config file controls the behaviour of agent-types such as langserve, controlling what endpoints are used\nkind: agentConfig\napiVersion: v1\ndefault:\n  stream: "{stem}/vac/streaming/{vector_name}"\n  invoke: "{stem}/vac/{vector_name}"\n\nlangserve:\n  stream: "{stem}/{vector_name}/stream"\n  invoke: "{stem}/{vector_name}/invoke"\n  input_schema: "{stem}/{vector_name}/input_schema"\n  output_schema: "{stem}/{vector_name}/output_schema"\n  config_schema: "{stem}/{vector_name}/config_schema"\n  batch: "{stem}/{vector_name}/batch"\n  stream_log: "{stem}/{vector_name}/stream_log"\n\nedmonbrain:\n  stream: "{stem}/vac/streaming/{vector_name}"\n  invoke: "{stem}/vac/{vector_name}"\n\nopeninterpreter:\n  stream: "{stem}/vac/streaming/{vector_name}"\n  invoke: "{stem}/vac/{vector_name}"\n\ncrewai:\n  stream: "{stem}/vac/streaming/{vector_name}"\n  invoke: "{stem}/vac/{vector_name}"\n'})}),"\n",(0,t.jsx)(n.h2,{id:"userconfig",children:"userConfig"}),"\n",(0,t.jsxs)(n.p,{children:["This lets you do user authentication by matching the tags within ",(0,t.jsx)(n.code,{children:"llm_config.yaml"})," with user email domains"]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-yaml",children:'kind: userConfig\napiVersion: v1\nuser_groups:\n  - name: "admin"\n    domain: "sunholo.com"\n    role: "ADMIN"\n    tags:\n      - "admin_user"\n\n  - name: "eduvac"\n    emails:\n      - "multivac@sunholo.com"\n    role: "eduvac"\n    tags:\n      - "eduvac"\n\n  # Example of another firm using both domain and specific emails\n  - name: "another_firm"\n    domain: "anotherfirm.com"\n    emails:\n      - "specialcase@anotherfirm.com"\n    role: "partner"\n    tags:\n      - "partner"\n\ndefault_user:\n  role: "USER"\n  tags:\n    - "user"\n\n'})}),"\n",(0,t.jsx)(n.h2,{id:"promptconfig",children:"promptConfig"}),"\n",(0,t.jsxs)(n.p,{children:["This file contains various prompts for a vector_name of a VAC.  It is preferred that the native ",(0,t.jsx)(n.a,{href:"https://langfuse.sunholo.com",children:"Langfuse prompt library"})," is used, but this yaml file is a backup if its not available via Langfuse."]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-yaml",children:"kind: promptConfig\napiVersion: v1\nprompts:\n  eduvac:\n    intro: |\n      You are an expert teacher versed with the latest techniques to enhance learning with your students.\n      Todays date is {the_date}\n      Please create an assignment for the student that will demonstrate their understanding of the text. \n    template: |\n      Answer the question below with the help of the following context.  \n      # Context\n      {metadata}\n      # End Context\n\n      This is the conversation so far\n      # Chat Summary\n      ...{chat_summary}\n      # Chat History\n      ...{chat_history}\n      # End of Chat History\n\n      If you have made an earlier plan in your chat history, \n      briefly restate it and update where you are in that plan to make sure to \n      keep yourself on track and to not forget the original purpose of your answers.\n\n      Question: {question}\n      Your Answer:\n    chat_summary: |\n      Summarise the conversation below:\n      # Chat History\n      {chat_history}\n      # End Chat History\n      Your Summary of the chat history above:\n    summarise_known_question: |\n      You are an teacher assistant to a student and teacher who has has this input from the student:\n      {question}\n\n      # Chat history (teacher and student)\n      {chat_history}\n      # End Chat History\n\n      # Context (what the student is learning)\n      {context}\n      # end context\n      Assess if the student has completed the latest tasks set by the teacher, \n      with recommendations on what the student and teacher should do next. \n\n\n      Your Summary:\n"})})]})}function u(e={}){const{wrapper:n}={...(0,o.R)(),...e.components};return n?(0,t.jsx)(n,{...e,children:(0,t.jsx)(d,{...e})}):d(e)}},8453:(e,n,a)=>{a.d(n,{R:()=>s,x:()=>r});var t=a(6540);const o={},i=t.createContext(o);function s(e){const n=t.useContext(i);return t.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function r(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(o):e.components||o:s(e.components),t.createElement(i.Provider,{value:n},e.children)}}}]);