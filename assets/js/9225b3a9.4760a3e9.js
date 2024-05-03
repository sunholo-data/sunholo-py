"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[950],{5690:(e,n,a)=>{a.r(n),a.d(n,{assets:()=>c,contentTitle:()=>r,default:()=>d,frontMatter:()=>o,metadata:()=>i,toc:()=>l});var t=a(4848),s=a(8453);const o={},r="Config files",i={id:"config",title:"Config files",description:"A main aim for the sunholo library is to have as much of the functionality needed for GenAI apps available via configuration files, rather than within the code.",source:"@site/docs/config.md",sourceDirName:".",slug:"/config",permalink:"/docs/config",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/config.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"Functions",permalink:"/docs/function-reference"}},c={},l=[{value:"llm_config.yaml",id:"llm_configyaml",level:2},{value:"cloud_run_urls.json",id:"cloud_run_urlsjson",level:2},{value:"agent_config.yaml",id:"agent_configyaml",level:2}];function u(e){const n={code:"code",h1:"h1",h2:"h2",p:"p",pre:"pre",...(0,s.R)(),...e.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(n.h1,{id:"config-files",children:"Config files"}),"\n",(0,t.jsxs)(n.p,{children:["A main aim for the ",(0,t.jsx)(n.code,{children:"sunholo"})," library is to have as much of the functionality needed for GenAI apps available via configuration files, rather than within the code."]}),"\n",(0,t.jsx)(n.p,{children:"This allows you to set up new instances of GenAI apps quickly, and experiment with new models, vectorstores and other features."}),"\n",(0,t.jsx)(n.p,{children:"There are various config files available that control different features such as VAC behaviour and user access.  This is very much still a work in progress so the format may change in the future."}),"\n",(0,t.jsx)(n.h2,{id:"llm_configyaml",children:"llm_config.yaml"}),"\n",(0,t.jsx)(n.p,{children:"This is the main day to day configuration file that is used to set LLMs, databases and VAC tags.  An example is shown here:"}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-yaml",children:'pirate_speak:\n  llm: openai\n  agent: langserve\n  display_name: Pirate Speak\n  tags: ["free"]\n  avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4\n  description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that will repeat back what you say but in a pirate accent.  Ooh argh me hearties!  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.\ncsv_agent:\n  llm: openai\n  agent: langserve\n  display_name: Titanic\n  tags: ["free"]\n  avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4\n  description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that lets you ask questions over structured data like a database.  In this case, a local database contains statistics from the Titanic disaster passengers.  Langchain templates cover many different GenAI use cases and all can be streamed to Multivac clients.\nrag_lance:\n  llm: openai\n  agent: langserve\n  display_name: Simple RAG\n  tags: ["free"]\n  avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4\n  description: A Langserve demo using a demo [Langchain Template](https://templates.langchain.com/) that lets you ask questions over unstructured data.\n  memory:\n    - lancedb-vectorstore:\n        vectorstore: lancedb\n        provider: LanceDB \nfinetuned_model:\n  llm: model_garden\n  agent: langserve\n  gcp_config:\n    project_id: model_garden_project\n    endpoint_id: 12345678\n    location: europe-west1\nimage_talk:\n  llm: vertex\n  model: gemini-1.0-pro-vision\n  agent: langserve\n  upload: \n    mime_types:\n      - image\n  display_name: Talk to Images\n  tags: ["free"]\n  avatar_url: https://avatars.githubusercontent.com/u/1342004?s=200&v=4\n  description: A picture is worth a thousand words, so upload your picture and ask your question to the Gemini Pro Vision model.  Images are remembered for your conversation until you upload another.  This offers powerful applications, which you can get a feel for via the [Gemini Pro Vision docs](https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal/design-multimodal-prompts) \neduvac:\n  llm: anthropic\n  model: claude-3-opus-20240229\n  agent: eduvac # needs to match multivac service name\n  agent_type: langserve\n  display_name: Edu-VAC\n  tags: ["free"] # set to "eduvac" if you want to restrict usage to only users tagged "eduvac" in users_config.yaml\n  avatar_url: ../public/eduvac.png\n  description: Educate yourself in your own personal documents via guided learning from Eduvac, the ever patient teacher bot. Use search filters to examine available syllabus or upload your own documents to get started.\n  upload:   # to accept uploads of private documents to a bucket\n    mime_types:\n      - all\n    buckets:\n      all: your-bucket\n  buckets:\n    raw: your-bucket\n  docstore: # this needs to be valid to have document storage\n    - alloydb-docstore:\n        type: alloydb\n  alloydb_config:\n    project_id: your-projectid\n    region: europe-west1\n    cluster: your-cluster\n    instance: primary-instance-1\nsample_vector:\n  llm: azure\n  model: gpt-4-turbo-1106-preview\n  agent: langserve\n  display_name: Sample vector for tests\n  avatar_url: https://avatars.githubusercontent.com/u/126733545?s=48&v=4\n  description: An Azure OpenAI example\n  memory:\n    - lancedb-vectorstore:\n        vectorstore: lancedb\n        provider: LanceDB \n  embedder:\n    llm: azure\n  azure:\n    azure_openai_endpoint: https://openai-central-se-amass.openai.azure.com/\n    openai_api_version: 2024-02-01\n    embed_model: text-embedding-ada-002 # or text-embedding-3-large\n'})}),"\n",(0,t.jsx)(n.h2,{id:"cloud_run_urlsjson",children:"cloud_run_urls.json"}),"\n",(0,t.jsx)(n.p,{children:"This is an auto-generated file oon Multivac that lets the VACs know where are other endpoints.  You can also specify this manually if you have deployed to localhost or otherwise."}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-json",children:'{\n    "agents":"https://agents-xxxx.a.run.app",\n    "chunker":"https://chunker-xxxx.a.run.app",\n    "embedder":"https://embedder-xxxx.a.run.app",\n    "litellm":"https://litellm-xxxx.a.run.app",\n    "slack":"https://slack-xxxx.a.run.app",\n    "unstructured":"https://unstructured-xxxx.a.run.app"\n}\n'})}),"\n",(0,t.jsx)(n.h2,{id:"agent_configyaml",children:"agent_config.yaml"}),"\n",(0,t.jsxs)(n.p,{children:["Once the URL is found via the ",(0,t.jsx)(n.code,{children:"cloud_run_urls.json"})," above, this configuration file sets up standard endpoints."]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-yaml",children:'# this config file controls the behaviour of agent-types such as langserve, controlling what endpoints are used\ndefault:\n  stream: "{stem}/stream"\n  invoke: "{stem}/invoke"\n\nlangserve:\n  stream: "{stem}/{vector_name}/stream"\n  invoke: "{stem}/{vector_name}/invoke"\n  input_schema: "{stem}/{vector_name}/input_schema"\n  output_schema: "{stem}/{vector_name}/output_schema"\n  config_schema: "{stem}/{vector_name}/config_schema"\n  batch: "{stem}/{vector_name}/batch"\n  stream_log: "{stem}/{vector_name}/stream_log"\n\nedmonbrain:\n  stream: "{stem}/qna/streaming/{vector_name}"\n  invoke: "{stem}/qna/{vector_name}"\n\nopeninterpreter:\n  stream: "{stem}/qna/streaming/{vector_name}"\n  invoke: "{stem}/qna/{vector_name}"\n\ncrewai:\n  stream: "{stem}/qna/streaming/{vector_name}"\n  invoke: "{stem}/qna/{vector_name}"\n'})})]})}function d(e={}){const{wrapper:n}={...(0,s.R)(),...e.components};return n?(0,t.jsx)(n,{...e,children:(0,t.jsx)(u,{...e})}):u(e)}},8453:(e,n,a)=>{a.d(n,{R:()=>r,x:()=>i});var t=a(6540);const s={},o=t.createContext(s);function r(e){const n=t.useContext(o);return t.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function i(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(s):e.components||s:r(e.components),t.createElement(o.Provider,{value:n},e.children)}}}]);