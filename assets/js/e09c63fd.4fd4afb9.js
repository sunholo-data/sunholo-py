"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[4987],{8867:(e,n,o)=>{o.r(n),o.d(n,{assets:()=>s,contentTitle:()=>i,default:()=>h,frontMatter:()=>a,metadata:()=>c,toc:()=>l});var t=o(4848),r=o(8453);const a={},i="Creating a grounded in Google Search VertexAI app",c={id:"howto/grounded_vertex",title:"Creating a grounded in Google Search VertexAI app",description:"This goes through how to make a Vertex AI app with grounding via Google Search.",source:"@site/docs/howto/grounded_vertex.md",sourceDirName:"howto",slug:"/howto/grounded_vertex",permalink:"/docs/howto/grounded_vertex",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/howto/grounded_vertex.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"Creating a Flask VAC app",permalink:"/docs/howto/flask_app"},next:{title:"Streaming",permalink:"/docs/howto/streaming"}},s={},l=[{value:"Bootstrap",id:"bootstrap",level:2},{value:"vacConfig",id:"vacconfig",level:2},{value:"vac_service.py",id:"vac_servicepy",level:2},{value:"Deploy",id:"deploy",level:2}];function d(e){const n={code:"code",h1:"h1",h2:"h2",li:"li",ol:"ol",p:"p",pre:"pre",...(0,r.R)(),...e.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(n.h1,{id:"creating-a-grounded-in-google-search-vertexai-app",children:"Creating a grounded in Google Search VertexAI app"}),"\n",(0,t.jsx)(n.p,{children:"This goes through how to make a Vertex AI app with grounding via Google Search."}),"\n",(0,t.jsx)(n.h2,{id:"bootstrap",children:"Bootstrap"}),"\n",(0,t.jsx)(n.p,{children:"This is common to most VACs:"}),"\n",(0,t.jsxs)(n.ol,{start:"0",children:["\n",(0,t.jsxs)(n.li,{children:["Install via ",(0,t.jsx)(n.code,{children:"pip install sunholo"})]}),"\n",(0,t.jsx)(n.li,{children:"Create a new git repository and browse to the root"}),"\n",(0,t.jsxs)(n.li,{children:["Run ",(0,t.jsx)(n.code,{children:"sunholo init new_project"}),' to create a project called "new_project"']}),"\n",(0,t.jsx)(n.li,{children:"This will create a new folder with an example project files."}),"\n",(0,t.jsxs)(n.li,{children:["Make your changes to the ",(0,t.jsx)(n.code,{children:"vac_service.py"})," file - specifically the ",(0,t.jsx)(n.code,{children:"vac"})," and ",(0,t.jsx)(n.code,{children:"vac_stream"})," functions"]}),"\n",(0,t.jsxs)(n.li,{children:["Modify the ",(0,t.jsx)(n.code,{children:"vacConfig"})," in ",(0,t.jsx)(n.code,{children:"config/vac_config.yaml"})," with new instances of your VAC."]}),"\n"]}),"\n",(0,t.jsx)(n.h2,{id:"vacconfig",children:"vacConfig"}),"\n",(0,t.jsxs)(n.p,{children:["This controls the configurations of the different instances that can all re-use the same code you create in the scripts below.  Each ",(0,t.jsx)(n.code,{children:"vac"})," entry lets you create new prompts, features and a unique memory namespaces (e.g. one vector strore per instance)"]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-yaml",children:"kind: vacConfig\napiVersion: v1\nvac:\n  my_grounded_vertex:\n    llm: vertex\n    model: gemini-1.5-pro-preview-0514\n    model_quick: gemini-1.5-flash-001\n    agent: vertex-genai # the underlying cloud run application\n    display_name: Grounded Google\n    display_name: Gemini with grounding via Google Search\n    grounding:\n      google_search: true\n#... add new instances here\n"})}),"\n",(0,t.jsx)(n.h2,{id:"vac_servicepy",children:"vac_service.py"}),"\n",(0,t.jsxs)(n.p,{children:["This is the guts of your GenAI application.  You can optionally create a batch ",(0,t.jsx)(n.code,{children:"vac()"})," function and/or a ",(0,t.jsx)(n.code,{children:"vac_stream()"})," function that will be invoked when calling the VAC endpoints.  Additional arguments will be passed to help with common GenAI application tasks."]}),"\n",(0,t.jsxs)(n.p,{children:["Here is an example file that is used when doing ",(0,t.jsx)(n.code,{children:"sunholo init new_project"})]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:'from sunholo.logging import setup_logging\nfrom sunholo.utils.config import load_config_key\n\n# VAC specific imports\nfrom sunholo.vertex import init_vertex, get_google_search_grounding\nfrom vertexai.preview.generative_models import GenerativeModel\n\nlog = setup_logging("template")\n\n#TODO: change this to a streaming VAC function\ndef vac_stream(question: str, vector_name, chat_history=[], callback=None, **kwargs):\n\n    grounded_model = create_model(vector_name)\n\n    # streaming model calls\n    response = grounded_model.generate_content(question, stream=True)\n\n    chunks = ""\n    for chunk in response:\n        try:\n            callback.on_llm_new_token(token=chunk.text)\n            chunks += chunk.text\n        except ValueError as err:\n            callback.on_llm_new_token(token=str(err))\n    \n    callback.on_llm_end(response=response)\n\n    chat_history.append({\n        "role":"ai", "content": chunks\n    })\n\n    metadata = {\n        "chat_history": chat_history\n    }\n\n    return {"answer": chunks, "metadata": metadata}\n\n\n#TODO: change this to a batch VAC function\ndef vac(question: str, vector_name, chat_history=[], **kwargs):\n\n    grounded_model = create_model(vector_name)\n\n    response = grounded_model.generate_content(question)\n\n    log.info(f"Got response: {response}")\n\n    return {"answer": response.text}\n\n\n# common model setup to both batching and streaming\ndef create_model(vector_name):\n    gcp_config = load_config_key("gcp_config", vector_name=vector_name, kind="vacConfig")\n\n    init_vertex(gcp_config)\n \n    model = load_config_key("model", vector_name=vector_name, kind="vacConfig")\n    google_search = get_google_search_grounding(vector_name)\n\n    # Create a gemini-pro model instance\n    # https://ai.google.dev/api/python/google/generativeai/GenerativeModel#streaming\n    rag_model = GenerativeModel(\n        model_name=model or "gemini-1.0-pro-002", tools=[google_search]\n    )\n\n    return rag_model\n'})}),"\n",(0,t.jsx)(n.h2,{id:"deploy",children:"Deploy"}),"\n",(0,t.jsx)(n.p,{children:"Run the Flask app locally to check it, assuming you are logged in locally with gcloud."}),"\n",(0,t.jsx)(n.p,{children:"#TODO"})]})}function h(e={}){const{wrapper:n}={...(0,r.R)(),...e.components};return n?(0,t.jsx)(n,{...e,children:(0,t.jsx)(d,{...e})}):d(e)}},8453:(e,n,o)=>{o.d(n,{R:()=>i,x:()=>c});var t=o(6540);const r={},a=t.createContext(r);function i(e){const n=t.useContext(a);return t.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function c(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:i(e.components),t.createElement(a.Provider,{value:n},e.children)}}}]);